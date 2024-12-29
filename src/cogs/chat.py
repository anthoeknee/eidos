import discord
from discord.ext import commands
from src.services.ai.dialog import DialogService
from src.utils.logger import Logger
from src.core.config import settings
from typing import List, Union, Dict, Any
from src.services.storage.valkey import ValkeyService


class ChatCog(commands.Cog):
    """
    A cog that handles chat interactions using the DialogService.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = Logger(name="ChatCog", level="INFO")
        super().__init__()
        self.category = "AI"
        self.emoji = "💬"
        self.description = "Enables chat interactions with the bot."
        self.valkey = None
        self.dialog_service = None  # Initialize here

    async def cog_load(self) -> None:
        """Initialize async components when the cog is loaded."""
        self.valkey = ValkeyService()
        await self.valkey.connect()  # Ensure connection is established
        self.dialog_service = DialogService(valkey=self.valkey)  # Pass valkey here
        await self.dialog_service.start()

    async def cog_unload(self) -> None:
        """Cleanup resources when the cog is unloaded."""
        if self.dialog_service:
            await self.dialog_service.stop()
        if self.valkey:
            await self.valkey.disconnect()

    async def _should_respond(self, message: discord.Message) -> bool:
        """
        Determine if the bot should respond to a message.
        """
        if message.author.bot:
            return False

        if message.content.startswith(settings.discord_command_prefix):
            return False

        if message.guild:
            # In a server, respond only to mentions or replies
            return self.bot.user.mentioned_in(message) or message.reference is not None
        else:
            # In a DM, respond to all messages
            return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listens for messages and responds using the DialogService.
        """
        if not await self._should_respond(message):
            self.logger.debug(
                f"Ignoring message from {message.author}: {message.content}"
            )
            return

        self.logger.debug(
            f"Processing message from {message.author}: {message.content}"
        )

        try:
            user_message: List[Union[str, Dict[str, Any]]] = [message.content]
            user_content_types: List[str] = ["text"]

            if message.attachments:
                for attachment in message.attachments:
                    user_message.append(
                        {
                            "url": attachment.url,
                            "metadata": {"type": attachment.content_type},
                        }
                    )
                    user_content_types.append(attachment.content_type)

            response = await self.dialog_service.generate_response(
                channel_id=str(message.channel.id),
                user_id=str(message.author.id),
                user_message=user_message,
                user_content_types=user_content_types,
            )

            # Simplified response handling
            response_text = response
            if isinstance(response, (list, tuple)):
                response_text = response[0]
            if isinstance(response_text, dict):
                response_text = response_text.get("content", "No response available.")

            # Ensure response is a string and clean it up
            response_text = str(response_text).strip("[]\"'\n ")

            # Split the text into chunks
            text_chunks = split_text_for_discord(response_text)

            # Send the text chunks and attachments
            for i, chunk in enumerate(text_chunks):
                if i == 0 and message.attachments:
                    # Send the first chunk with attachments
                    await message.reply(
                        chunk,
                        files=[
                            await attachment.to_file()
                            for attachment in message.attachments
                        ],
                    )
                else:
                    # Send subsequent chunks without attachments
                    await message.reply(chunk)

            self.logger.debug(f"Replied to {message.author} with: {response_text}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            await message.reply("I encountered an error processing your request.")


def split_text_for_discord(text: str, max_length: int = 1900) -> List[str]:
    """
    Splits a string into chunks suitable for sending in Discord messages,
    preserving formatting as much as possible.

    Args:
        text: The string to split.
        max_length: The maximum length of each chunk (default: 1900).

    Returns:
        A list of strings, each representing a chunk of the original text.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""
    sentences = text.split(". ")  # Split by sentences

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 <= max_length:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    # If splitting by sentences doesn't work, split by lines
    if not chunks:
        current_chunk = ""
        lines = text.splitlines()
        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + "\n"
        if current_chunk:
            chunks.append(current_chunk.strip())

    # If splitting by lines doesn't work, split by words
    if not chunks:
        current_chunk = ""
        words = text.split(" ")
        for word in words:
            if len(current_chunk) + len(word) + 1 <= max_length:
                current_chunk += word + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word + " "
        if current_chunk:
            chunks.append(current_chunk.strip())

    # If all else fails, split by character count
    if not chunks:
        for i in range(0, len(text), max_length):
            chunks.append(text[i : i + max_length])

    return chunks


async def setup(bot: commands.Bot):
    """Setup function to add the cog to the bot."""
    cog = ChatCog(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
