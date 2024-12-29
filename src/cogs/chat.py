import discord
from discord.ext import commands
from src.services.ai.dialog import DialogService
from src.utils.logger import Logger
from src.core.config import settings
from typing import List, Union, Dict, Any
import json


class ChatCog(commands.Cog):
    """
    A cog that handles chat interactions using the DialogService.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dialog_service = DialogService()
        self.logger = Logger(name="ChatCog", level="INFO")
        super().__init__()
        self.category = "AI"
        self.emoji = "💬"
        self.description = "Enables chat interactions with the bot."

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

            self.logger.debug(
                f"User message: {user_message}, content types: {user_content_types}"
            )

            response = await self.dialog_service.generate_response(
                channel_id=str(message.channel.id),
                user_id=str(message.author.id),
                user_message=user_message,
                user_content_types=user_content_types,
            )

            self.logger.debug(f"Response from DialogService: {response}")

            if response:
                await message.reply(response[0])
                self.logger.debug(f"Replied to {message.author} with: {response[0]}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            await message.reply("I encountered an error processing your request.")


async def setup(bot: commands.Bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(ChatCog(bot))
