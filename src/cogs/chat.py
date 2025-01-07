import discord
from discord.ext import commands
from src.services.ai.memory.short_term import ShortTermMemory
from src.services.ai.providers import GoogleAIProvider
from src.services.ai.memory.long_term import LongTermMemory
import asyncio
import logging

logger = logging.getLogger(__name__)


class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._memory_task = None
        self._long_term_memory = None
        self._conversation_contexts = {}  # Track active conversation contexts

    async def cog_load(self):
        logger.info("Loading ChatCog...")
        try:
            # Get the database service
            db_service = await self.bot.get_service("database")
            if not db_service:
                logger.error("Database service not available")
                raise RuntimeError("Database service not initialized")

            # Get the long-term memory service
            self._long_term_memory = await self.bot.get_service("ai.long_term_memory")
            if not self._long_term_memory:
                logger.error("Long-term memory service returned None")
                raise RuntimeError("Long-term memory service not initialized")

            logger.info("Successfully loaded required services")

            # Add the memory task listener
            self.bot.add_listener(self.start_memory_task, "on_ready")
            logger.info("Memory task will start when bot is ready")

        except Exception as e:
            logger.error(f"Error in cog_load: {str(e)}", exc_info=True)
            raise

    async def start_memory_task(self):
        """Start the memory processing task when the bot is ready."""
        if not self._memory_task:
            self._memory_task = asyncio.create_task(self._process_memories())
            logger.info("Memory processing task started")

    async def cog_unload(self):
        if self._memory_task:
            self._memory_task.cancel()
            try:
                await self._memory_task
            except asyncio.CancelledError:
                pass
            self._memory_task = None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        short_term_memory = await self.bot.get_service("ai.short_term_memory")
        long_term_memory = await self.bot.get_service("ai.long_term_memory")

        if not all([short_term_memory, long_term_memory]):
            return

        # Enhanced message processing
        channel_id = str(message.channel.id)

        # Store message with enhanced metadata
        await short_term_memory.add_message(message)

        # Process attachments with better context
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith("image/"):
                    context = {
                        "author": message.author.name,
                        "channel_name": getattr(message.channel, "name", "DM"),
                        "timestamp": message.created_at.isoformat(),
                        "message_content": message.content,
                        "mentions": [user.name for user in message.mentions],
                    }

                    await long_term_memory.store_image_memory(
                        channel_id,
                        attachment.url,
                        f"Image shared by {message.author.name} in {context['channel_name']} with message: {message.content}",
                        metadata=context,
                    )

        # Handle responses
        should_respond = (
            isinstance(message.channel, discord.DMChannel)
            or self.bot.user.mentioned_in(message)
            or (
                message.reference
                and message.reference.resolved
                and message.reference.resolved.author.id == self.bot.user.id
            )
        )

        # Handle case where prefix might be a list
        prefix = self.bot.command_prefix(self.bot, message)
        if isinstance(prefix, list):
            prefix = prefix[0]  # Take the first prefix if it's a list

        if should_respond and not message.content.startswith(prefix):
            await self.handle_ai_response(message)

    def user_is_mentioned(self, message: discord.Message) -> bool:
        return self.bot.user.mentioned_in(message)

    async def handle_ai_response(self, message: discord.Message):
        try:
            print("Starting AI response generation")
            short_term_memory = await self.bot.get_service("ai.short_term_memory")
            google_ai = await self.bot.get_service("ai.google")
            long_term_memory = await self.bot.get_service("ai.long_term_memory")

            if not all([short_term_memory, google_ai, long_term_memory]):
                print("Failed to get required services")
                await message.channel.send(
                    "I'm having trouble accessing my required services. Please try again later."
                )
                return

            channel_id = str(message.channel.id)

            # Get recent conversation context
            messages = await short_term_memory.get_messages(channel_id)

            # Retrieve relevant long-term memories with error handling
            relevant_memories = []
            try:
                relevant_memories = await long_term_memory.search_memories(
                    channel_id=channel_id,
                    query=message.content,
                    limit=3,
                    min_importance=0.6,
                )
            except Exception as e:
                logger.warning(f"Could not access long-term memories: {e}")
                # Continue without long-term memories rather than failing completely

            # Build enhanced context
            memory_context = ""
            if relevant_memories:
                memory_context = "Relevant past context:\n" + "\n".join(
                    [
                        f"- {mem['content']} (Importance: {mem['metadata']['importance_score']:.2f})"
                        for mem in relevant_memories
                    ]
                )

            # Get conversation metadata
            conversation_meta = await short_term_memory.get_metadata(channel_id)

            system_prompt = """You are a helpful Discord bot assistant with both short-term and long-term memory.
            Use the provided conversation context and relevant memories to give informed, contextual responses.
            Keep responses natural and conversational while being helpful and informative."""

            # Build enhanced conversation history
            conversation = "\n".join(
                [
                    f"{'Bot: ' if msg.startswith(self.bot.user.name) else 'User: '}{msg}"
                    for msg in messages
                ]
            )

            # Construct full prompt with enhanced context
            full_prompt = f"{system_prompt}\n\n{memory_context}\n\nCurrent conversation:\n{conversation}\n\nUser: {message.content}\nBot:"

            print("Generating response with enhanced context...")
            response = await google_ai.generate(prompt=full_prompt)

            if response:
                # Store bot's response in memory systems
                # Create a fake message object for memory storage
                bot_message = type(
                    "FakeMessage",
                    (),
                    {
                        "content": response,
                        "author": self.bot.user,
                        "channel": message.channel,
                        "created_at": discord.utils.utcnow(),
                    },
                )

                await short_term_memory.add_message(bot_message)

                # Add to long-term memory buffer
                await long_term_memory.add_to_buffer(
                    channel_id, f"{self.bot.user.name}: {response}"
                )

                print(f"Sending response: {response[:100]}...")
                await message.channel.send(response)
            else:
                print("No response generated")
                await message.channel.send(
                    "I apologize, but I couldn't generate a response."
                )

        except Exception as e:
            logger.error(f"Error in handle_ai_response: {str(e)}", exc_info=True)
            await message.channel.send(
                "I encountered an error while processing your message. Please try again later."
            )

    async def _process_memories(self):
        """Background task to process long-term memories."""
        try:
            await asyncio.sleep(300)  # Initial delay of 5 minutes after bot start
            while True:
                if self._long_term_memory and self._long_term_memory.memory_buffer:
                    for channel_id in list(self._long_term_memory.memory_buffer.keys()):
                        # Only process if there are actually messages in the buffer
                        if (
                            len(
                                self._long_term_memory.memory_buffer.get(channel_id, [])
                            )
                            > 0
                        ):
                            await self._long_term_memory._check_process_memory(
                                channel_id
                            )
                await asyncio.sleep(
                    300
                )  # Check every 5 minutes instead of every minute
        except asyncio.CancelledError:
            logger.info("Memory processing task cancelled")
        except Exception as e:
            logger.error(f"Error in memory processing task: {e}")


async def setup(bot):
    await bot.add_cog(ChatCog(bot))
