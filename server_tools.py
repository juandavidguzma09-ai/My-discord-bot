import discord
from discord.ext import commands
import datetime
import io
import requests

THEME_COLOR = 0x2b2d31

def build_embed(title, description=None, fields=None):
    embed = discord.Embed(title=title, description=description, color=THEME_COLOR)
    embed.timestamp = datetime.datetime.now()
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
    return embed

class ServerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------------------
    # SERVER INFO & STATS
    # ----------------------------
    @commands.hybrid_command(name="serverinfo", description="Muestra información del servidor")
    async def serverinfo(self, ctx):
        g = ctx.guild
        embed = build_embed(f"Info: {g.name}", fields={
            "ID": g.id,
            "Owner": g.owner,
            "Miembros": g.member_count,
            "Roles": len(g.roles),
            "Canales": len(g.channels),
            "Creación": g.created_at.strftime("%Y-%m-%d")
        })
        embed.set_thumbnail(url=g.icon.url if g.icon else "")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="membercount", description="Cantidad de miembros humanos y bots")
    async def membercount(self, ctx):
        humans = len([m for m in ctx.guild.members if not m.bot])
        bots = len([m for m in ctx.guild.members if m.bot])
        await ctx.send(embed=build_embed("Miembros del Servidor", f"Humanos: {humans}\nBots: {bots}"))

    @commands.hybrid_command(name="roles", description="Lista los roles del servidor")
    async def roles(self, ctx):
        roles = [r.name for r in ctx.guild.roles if r.name != "@everyone"]
        await ctx.send(embed=build_embed(f"Roles ({len(roles)})", ", ".join(roles)))

    @commands.hybrid_command(name="channels", description="Lista los canales del servidor")
    async def channels(self, ctx):
        chs = [c.name for c in ctx.guild.channels]
        await ctx.send(embed=build_embed(f"Canales ({len(chs)})", ", ".join(chs)))

    @commands.hybrid_command(name="emojis", description="Lista los emojis del servidor")
    async def emojis(self, ctx):
        emojis = [str(e) for e in ctx.guild.emojis]
        await ctx.send(embed=build_embed(f"Emojis ({len(emojis)})", " ".join(emojis) if emojis else "No hay emojis"))

    @commands.hybrid_command(name="stickers", description="Lista stickers del servidor")
    async def stickers(self, ctx):
        stickers = [s.name for s in ctx.guild.stickers]
        await ctx.send(embed=build_embed(f"Stickers ({len(stickers)})", ", ".join(stickers) if stickers else "No hay stickers"))

    @commands.hybrid_command(name="icon", description="Muestra el icono del servidor")
    async def icon(self, ctx):
        if ctx.guild.icon:
            await ctx.send(embed=build_embed(f"Icono: {ctx.guild.name}").set_image(url=ctx.guild.icon.url))
        else:
            await ctx.send("Este servidor no tiene icono.")

    @commands.hybrid_command(name="banner", description="Muestra el banner del servidor")
    async def banner(self, ctx):
        if ctx.guild.banner:
            await ctx.send(embed=build_embed(f"Banner: {ctx.guild.name}").set_image(url=ctx.guild.banner.url))
        else:
            await ctx.send("Este servidor no tiene banner.")

    @commands.hybrid_command(name="boosts", description="Información de boosts del servidor")
    async def boosts(self, ctx):
        await ctx.send(embed=build_embed("Boosts", f"Nivel de boost: {ctx.guild.premium_tier}\nBoosters: {ctx.guild.premium_subscription_count}"))

    @commands.hybrid_command(name="firstmessage", description="Obtiene el primer mensaje de un canal")
    async def firstmessage(self, ctx):
        msg = [m async for m in ctx.channel.history(limit=1, oldest_first=True)][0]
        await ctx.send(embed=build_embed("Primer mensaje", f"[Click para ver]({msg.jump_url})"))

    # ----------------------------
    # AUTO-ROLE Y WELCOME
    # ----------------------------
    @commands.hybrid_command(name="autorole", description="Activa auto-role para nuevos miembros")
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx, role: discord.Role):
        self.bot.autorole = getattr(self.bot, "autorole", {})
        self.bot.autorole[ctx.guild.id] = role.id
        await ctx.send(embed=build_embed("Auto-Role", f"{role.name} será dado automáticamente a nuevos miembros"))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_id = getattr(self.bot, "autorole", {}).get(member.guild.id)
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)

    # ----------------------------
    # MESSAGE TOOLS
    # ----------------------------
    @commands.hybrid_command(name="say", description="Hace que el bot diga algo")
    async def say(self, ctx, *, message):
        await ctx.send(message)

    @commands.hybrid_command(name="embed", description="Crea un embed con un mensaje")
    async def embed(self, ctx, *, message):
        await ctx.send(embed=build_embed("Embed", message))

    @commands.hybrid_command(name="poll", description="Crea una encuesta")
    async def poll(self, ctx, *, question):
        msg = await ctx.send(embed=build_embed("Encuesta", question))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    # ----------------------------
    # BACKUP DE CANALES (TXT)
    # ----------------------------
    @commands.hybrid_command(name="archive", description="Descarga mensajes del canal en TXT")
    @commands.has_permissions(manage_channels=True)
    async def archive(self, ctx, limit: int = 1000):
        buffer = io.StringIO()
        messages = [m async for m in ctx.channel.history(limit=limit)]
        messages.reverse()
        buffer.write(f"ARCHIVO DE CHAT: {ctx.channel.name} | {datetime.datetime.now()}\n\n")
        for msg in messages:
            buffer.write(f"[{msg.created_at}] {msg.author}: {msg.content}\n")
        buffer.seek(0)
        await ctx.send(file=discord.File(io.BytesIO(buffer.getvalue().encode()), filename=f"archive-{ctx.channel.name}.txt"))
