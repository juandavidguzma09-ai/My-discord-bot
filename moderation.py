import discord
from discord.ext import commands
import asyncio
import datetime
import io
import re

THEME_COLOR = 0x2b2d31

def build_embed(title, description=None, fields=None):
    embed = discord.Embed(title=title, description=description, color=THEME_COLOR)
    embed.timestamp = datetime.datetime.now()
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=True)
    return embed

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}
        self.edit_snipes = {}
        self.warns = {}

    # ---------------------------------------
    # EVENTOS SNIPE
    # ---------------------------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        self.snipes[message.channel.id] = message

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot: return
        self.edit_snipes[before.channel.id] = (before, after)

    # ---------------------------------------
    # BAN / KICK / MUTE / JAIL / WARN
    # ---------------------------------------
    @commands.hybrid_command(name="ban", description="Banea a un usuario.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason"):
        await member.ban(reason=reason)
        await ctx.send(embed=build_embed("Ban Executed", f"{member} baneado. Razón: {reason}"))

    @commands.hybrid_command(name="kick", description="Expulsa a un usuario.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason"):
        await member.kick(reason=reason)
        await ctx.send(embed=build_embed("Kick Executed", f"{member} expulsado. Razón: {reason}"))

    @commands.hybrid_command(name="mute", description="Silencia a un usuario.")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: int = 0):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await ctx.guild.create_role(name="Muted")
            for ch in ctx.guild.channels:
                await ch.set_permissions(mute_role, send_messages=False, speak=False)
        await member.add_roles(mute_role)
        await ctx.send(embed=build_embed("Muted", f"{member} silenciado."))
        if duration > 0:
            await asyncio.sleep(duration*60)
            await member.remove_roles(mute_role)
            await ctx.send(embed=build_embed("Unmute", f"{member} ya puede hablar."))

    @commands.hybrid_command(name="unmute", description="Quita el silencio.")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if mute_role in member.roles:
            await member.remove_roles(mute_role)
            await ctx.send(embed=build_embed("Unmute", f"{member} ya puede hablar."))

    @commands.hybrid_command(name="warn", description="Amonesta a un usuario.")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason"):
        if member.id not in self.warns: self.warns[member.id] = []
        self.warns[member.id].append(reason)
        await ctx.send(embed=build_embed("Warn", f"{member} advertido. Razón: {reason}"))

    @commands.hybrid_command(name="warns", description="Muestra advertencias de un usuario.")
    async def warns(self, ctx, member: discord.Member):
        user_warns = self.warns.get(member.id, [])
        if not user_warns: return await ctx.send(embed=build_embed("Warns", f"{member} no tiene advertencias."))
        await ctx.send(embed=build_embed(f"Warns de {member}", "\n".join(user_warns)))

    @commands.hybrid_command(name="clearwarns", description="Borra todas las advertencias de un usuario.")
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member):
        self.warns[member.id] = []
        await ctx.send(embed=build_embed("Clear Warns", f"Todas las advertencias de {member} eliminadas."))

    @commands.hybrid_command(name="jail", description="Aísla a un usuario en un rol de castigo.")
    @commands.has_permissions(administrator=True)
    async def jail(self, ctx, member: discord.Member):
        jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
        if not jail_role:
            jail_role = await ctx.guild.create_role(name="Jailed")
            for ch in ctx.guild.channels:
                await ch.set_permissions(jail_role, send_messages=False, read_messages=False)
        await member.edit(roles=[jail_role])
        await ctx.send(embed=build_embed("Jail", f"{member} encarcelado."))

    @commands.hybrid_command(name="unjail", description="Libera del rol de castigo.")
    @commands.has_permissions(administrator=True)
    async def unjail(self, ctx, member: discord.Member):
        jail_role = discord.utils.get(ctx.guild.roles, name="Jailed")
        if jail_role in member.roles:
            await member.remove_roles(jail_role)
            await ctx.send(embed=build_embed("Unjail", f"{member} liberado."))

    # ---------------------------------------
    # PURGE / MASS DELETE / ADVANCED PURGE
    # ---------------------------------------
    @commands.hybrid_command(name="purge", description="Elimina mensajes recientes.")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit: int = 100):
        deleted = await ctx.channel.purge(limit=limit)
        await ctx.send(embed=build_embed("Purge", f"{len(deleted)} mensajes eliminados."), delete_after=5)

    @commands.hybrid_command(name="purge_match", description="Elimina mensajes que contengan una palabra.")
    @commands.has_permissions(manage_messages=True)
    async def purge_match(self, ctx, limit: int, *, word: str):
        deleted = await ctx.channel.purge(limit=limit, check=lambda m: word.lower() in m.content.lower())
        await ctx.send(embed=build_embed("Purge Match", f"{len(deleted)} mensajes eliminados con '{word}'."), delete_after=5)

    @commands.hybrid_command(name="purgebots", description="Elimina mensajes de bots.")
    @commands.has_permissions(manage_messages=True)
    async def purgebots(self, ctx, limit: int = 100):
        deleted = await ctx.channel.purge(limit=limit, check=lambda m: m.author.bot)
        await ctx.send(embed=build_embed("Purge Bots", f"{len(deleted)} mensajes de bots eliminados."), delete_after=5)

    @commands.hybrid_command(name="purgelinks", description="Elimina mensajes que contengan links.")
    @commands.has_permissions(manage_messages=True)
    async def purgelinks(self, ctx, limit: int = 100):
        url_regex = re.compile(r'https?://')
        deleted = await ctx.channel.purge(limit=limit, check=lambda m: url_regex.search(m.content))
        await ctx.send(embed=build_embed("Purge Links", f"{len(deleted)} mensajes con links eliminados."), delete_after=5)

    @commands.hybrid_command(name="purgeimages", description="Elimina mensajes con imágenes.")
    @commands.has_permissions(manage_messages=True)
    async def purgeimages(self, ctx, limit: int = 100):
        deleted = await ctx.channel.purge(limit=limit, check=lambda m: m.attachments)
        await ctx.send(embed=build_embed("Purge Images", f"{len(deleted)} mensajes con imágenes eliminados."), delete_after=5)

    # ---------------------------------------
    # ROLE MANAGEMENT
    # ---------------------------------------
    @commands.hybrid_command(name="roleadd", description="Añade un rol a un usuario.")
    @commands.has_permissions(manage_roles=True)
    async def roleadd(self, ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        await ctx.send(embed=build_embed("Role Add", f"{role} añadido a {member}"))

    @commands.hybrid_command(name="roleremove", description="Quita un rol de un usuario.")
    @commands.has_permissions(manage_roles=True)
    async def roleremove(self, ctx, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        await ctx.send(embed=build_embed("Role Remove", f"{role} removido de {member}"))

    @commands.hybrid_command(name="roleall", description="Añade un rol a todos los usuarios humanos.")
    @commands.has_permissions(administrator=True)
    async def roleall(self, ctx, role: discord.Role):
        count = 0
        for m in ctx.guild.members:
            if not m.bot and role not in m.roles:
                try:
                    await m.add_roles(role)
                    count += 1
                    await asyncio.sleep(0.5)
                except: pass
        await ctx.send(embed=build_embed("Role All", f"{role} añadido a {count} usuarios"))

    @commands.hybrid_command(name="roleremoveall", description="Quita un rol a todos los usuarios humanos.")
    @commands.has_permissions(administrator=True)
    async def roleremoveall(self, ctx, role: discord.Role):
        count = 0
        for m in ctx.guild.members:
            if not m.bot and role in m.roles:
                try:
                    await m.remove_roles(role)
                    count += 1
                    await asyncio.sleep(0.5)
                except: pass
        await ctx.send(embed=build_embed("Role Remove All", f"{role} removido de {count} usuarios"))

    # ---------------------------------------
    # CHANNEL MANAGEMENT
    # ---------------------------------------
    @commands.hybrid_command(name="rename", description="Renombra el canal.")
    @commands.has_permissions(manage_channels=True)
    async def rename(self, ctx, *, new_name):
        await ctx.channel.edit(name=new_name)
        await ctx.send(embed=build_embed("Rename", f"Canal renombrado a {new_name}"))

    @commands.hybrid_command(name="slowmode", description="Aplica slowmode al canal en segundos.")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=build_embed("Slowmode", f"Slowmode de {seconds}s aplicado."))

    @commands.hybrid_command(name="lock", description="Bloquea el canal para todos.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(embed=build_embed("Lock", "Canal bloqueado."))

    @commands.hybrid_command(name="unlock", description="Desbloquea el canal para todos.")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(embed=build_embed("Unlock", "Canal desbloqueado."))

# Cargar el cog
async def setup(bot):
    await bot.add_cog(Moderation(bot))
