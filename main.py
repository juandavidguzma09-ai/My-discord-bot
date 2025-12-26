import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX", "$")

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Carga automática de cogs
@bot.event
async def setup_hook():
    await bot.load_extension("cogs.moderation")
    print(">> Cog de moderación cargado.")

# Evento ready
@bot.event
async def on_ready():
    print(f">> Bot online: {bot.user} | ID: {bot.user.id}")

bot.run(TOKEN)
