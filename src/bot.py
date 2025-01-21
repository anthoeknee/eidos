# src/bot.py
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="eidos!", intents=intents)
