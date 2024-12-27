import discord
from discord.ext import commands
from typing import List

from src.services.llm.personality import PersonalityManager
from src.services.manager import ServiceManager
from src.utils import logger

log = logger.setup_logger("llm_events")


class LLMEvents:
    """Handles LLM-related events and commands."""

    def __init__(
        self,
        bot: commands.Bot,
        service_manager: ServiceManager,
        personality_config=None,
    ):
        self.bot = bot
        self.services = service_manager

        # Initialize LLM service with specific personality
        if hasattr(self.services.llm, "personality"):
            self.services.llm.personality = PersonalityManager(personality_config)

        self._register_commands()
        self._register_events()

    @classmethod
    async def create(cls, bot: commands.Bot, service_manager: ServiceManager):
        """Factory method to properly initialize the LLMEvents class."""
        instance = cls(bot, service_manager)
        await instance.services.llm.initialize()
        return instance

    def _register_commands(self):
        @self.bot.command(name="ask")
        async def ask(ctx, *, question: str):
            """Ask the LLM a question."""
            try:
                response = await self.services.llm.generate_text(question)
                await ctx.send(response)
            except Exception as e:
                log.error(f"Error in ask command: {e}")
                await ctx.send("Sorry, I encountered an error processing your request.")

        @self.bot.command(name="set_personality")
        async def set_personality(ctx, personality_name: str):
            """Switch the bot's personality."""
            try:
                # Import personalities dynamically
                from src.services.llm.personality_configs import EIDOS_PERSONALITY

                personalities = {
                    "eidos": EIDOS_PERSONALITY,
                }

                if personality_name.lower() not in personalities:
                    await ctx.send(
                        f"Available personalities: {', '.join(personalities.keys())}"
                    )
                    return

                # Update the personality
                self.services.llm.personality = PersonalityManager(
                    personalities[personality_name.lower()]
                )

                await ctx.send(f"Switched to {personality_name} personality!")

            except Exception as e:
                log.error(f"Error switching personality: {e}")
                await ctx.send("Failed to switch personality.")

    def _register_events(self):
        @self.bot.event
        async def on_message(message: discord.Message):
            # Ignore messages from bots (including self)
            if message.author.bot:
                return

            # Process commands first to ensure they work
            await self.bot.process_commands(message)

            # Ignore application commands (/, @mention) and prefix commands
            if message.type != discord.MessageType.default:
                return

            should_respond = False

            # Handle DMs
            if isinstance(message.channel, discord.DMChannel):
                should_respond = True

            # Handle server messages
            else:
                # Respond only if the bot is mentioned or message is a reply to the bot
                is_mentioned = self.bot.user in message.mentions
                is_reply_to_bot = (
                    message.reference
                    and message.reference.resolved
                    and message.reference.resolved.author.id == self.bot.user.id
                )

                should_respond = is_mentioned or is_reply_to_bot

            if should_respond:
                try:
                    # Extract mentions information
                    mentions = []

                    # User mentions
                    for user in message.mentions:
                        mentions.append(
                            {
                                "type": "user",
                                "id": str(user.id),
                                "name": user.display_name,
                                "username": user.name,
                                "bot_id": str(self.bot.user.id),
                            }
                        )

                    # Role mentions
                    for role in message.role_mentions:
                        mentions.append(
                            {"type": "role", "id": str(role.id), "name": role.name}
                        )

                    # Channel mentions
                    for channel in message.channel_mentions:
                        mentions.append(
                            {
                                "type": "channel",
                                "id": str(channel.id),
                                "name": channel.name,
                            }
                        )

                    # Get message attachments info
                    attachments = [
                        {
                            "url": att.url,
                            "filename": att.filename,
                            "content_type": att.content_type,
                            "size": att.size,
                            "width": getattr(att, "width", None),
                            "height": getattr(att, "height", None),
                            "description": getattr(att, "description", None),
                        }
                        for att in message.attachments
                    ]

                    # Get message reference/reply info
                    reference = None
                    if message.reference and message.reference.resolved:
                        ref_msg = message.reference.resolved
                        reference = {
                            "content": ref_msg.content,
                            "author": {
                                "name": ref_msg.author.display_name,
                                "username": ref_msg.author.name,
                                "id": str(ref_msg.author.id),
                            },
                            "attachments": [
                                {
                                    "url": att.url,
                                    "filename": att.filename,
                                    "content_type": att.content_type
                                    if hasattr(att, "content_type")
                                    else None,
                                }
                                for att in ref_msg.attachments
                            ],
                            "id": str(ref_msg.id),
                            "timestamp": ref_msg.created_at.isoformat(),
                        }

                    channel_info = {
                        "name": message.channel.name
                        if hasattr(message.channel, "name")
                        else "DM",
                        "type": str(message.channel.type),
                        "category": message.channel.category.name
                        if hasattr(message.channel, "category")
                        and message.channel.category
                        else None,
                        "discord_channel": message.channel,
                    }

                    response = await self.services.llm.process_message(
                        content=message.content,
                        author_id=str(message.author.id),
                        channel_id=str(message.channel.id),
                        attachments=attachments,
                        mentions=mentions,
                        reference=reference,
                        user_info={
                            "name": message.author.display_name,
                            "username": message.author.name,
                            "roles": [role.name for role in message.author.roles]
                            if hasattr(message.author, "roles")
                            else None,
                        },
                        bot_info={
                            "name": message.guild.me.display_name
                            if message.guild
                            else self.bot.user.name,
                            "username": self.bot.user.name,
                        },
                        channel_info=channel_info,
                    )

                    # Split and send response
                    chunks = self.split_message(response)
                    for chunk in chunks:
                        await message.reply(chunk)

                except Exception as e:
                    log.error(f"Error processing message: {str(e)}", exc_info=True)

    def split_message(self, content: str, max_length: int = 2000) -> List[str]:
        """Split a message into chunks that fit Discord's character limit.

        Args:
            content: The message content to split
            max_length: Maximum length of each chunk (default: 2000 for Discord)

        Returns:
            List of message chunks
        """
        # If content is short enough, return as single message
        if len(content) <= max_length:
            return [content]

        chunks = []
        current_chunk = ""

        # Split on natural boundaries (paragraphs, sentences, then words)
        paragraphs = content.split("\n\n")

        for paragraph in paragraphs:
            # If paragraph alone exceeds limit, split into sentences
            if len(paragraph) > max_length:
                sentences = paragraph.split(". ")
                for sentence in sentences:
                    # If sentence alone exceeds limit, split on words
                    if len(sentence) > max_length:
                        words = sentence.split(" ")
                        for word in words:
                            if len(current_chunk) + len(word) + 1 > max_length:
                                chunks.append(current_chunk.strip())
                                current_chunk = word + " "
                            else:
                                current_chunk += word + " "
                    else:
                        if len(current_chunk) + len(sentence) + 2 > max_length:
                            chunks.append(current_chunk.strip())
                            current_chunk = sentence + ". "
                        else:
                            current_chunk += sentence + ". "
            else:
                if len(current_chunk) + len(paragraph) + 2 > max_length:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n\n"
                else:
                    current_chunk += paragraph + "\n\n"

        # Add any remaining content
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
