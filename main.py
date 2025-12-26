import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = "$"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# --- Carga de Cogs ---
async def load_cogs():
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.server_tools")

@bot.event
async def on_ready():
    print(f">> Bot online: {bot.user}")

@bot.command(name="help")
async def help_command(ctx):
    msg = (
        "**Prefijo:** `$`\n"
        "**Slash:** `/`\n\n"
        "**Comandos disponibles en Moderation y Server Tools.**"
    )
    await ctx.send(msg)

# --- Main ---
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())
