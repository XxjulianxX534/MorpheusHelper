from typing import Optional

from discord import Role, Guild, Member, Forbidden, HTTPException
from discord.ext import commands
from discord.ext.commands import Cog, Bot, guild_only, Context

from database import run_in_thread
from models.mod import Warn, Report
from models.settings import Settings
from translations import translations
from util import permission_level, ADMINISTRATOR, send_to_changelog, SUPPORTER


async def configure_role(ctx: Context, role_name: str, role: Optional[Role]):
    guild: Guild = ctx.guild
    if role is None:
        role = guild.get_role(await run_in_thread(Settings.get, int, role_name + "_role"))
        if role is None:
            await ctx.send(translations.no_role_set)
        else:
            await ctx.send(f"`@{role}` ({role.id})")
    else:
        await run_in_thread(Settings.set, int, role_name + "_role", role.id)
        await ctx.send(translations.role_set)
        await send_to_changelog(ctx.guild, getattr(translations, "f_log_role_set_" + role_name)(role.name, role.id))


class ModCog(Cog, name="Mod Tools"):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(name="roles")
    @permission_level(ADMINISTRATOR)
    @guild_only()
    async def roles(self, ctx: Context):
        """
        configure roles
        """

        if ctx.invoked_subcommand is None:
            await ctx.send_help(ModCog.roles)

    @roles.command(name="administrator", aliases=["admin"])
    async def set_admin(self, ctx: Context, role: Optional[Role]):
        """
        set administrator role
        """

        await configure_role(ctx, "admin", role)

    @roles.command(name="moderator", aliases=["mod"])
    async def set_mod(self, ctx: Context, role: Optional[Role]):
        """
        set moderator role
        """

        await configure_role(ctx, "mod", role)

    @roles.command(name="supporter", aliases=["supp"])
    async def set_supp(self, ctx: Context, role: Optional[Role]):
        """
        set supporter role
        """

        await configure_role(ctx, "supp", role)

    @roles.command(name="team")
    async def set_team(self, ctx: Context, role: Optional[Role]):
        """
        set team role
        """

        await configure_role(ctx, "team", role)

    @roles.command(name="mute")
    async def set_mute(self, ctx: Context, role: Optional[Role]):
        """
        set mute role
        """

        await configure_role(ctx, "mute", role)

    @commands.command(name="report")
    @guild_only()
    async def report(self, ctx: Context, member: Member, *, reason: str):
        """
        report a member
        """

        await run_in_thread(Report.create, member.id, ctx.author.id, reason)
        await ctx.send(translations.reported_response)
        await send_to_changelog(ctx.guild, translations.f_log_reported(ctx.author.mention, member.mention, reason))

    @commands.command(name="warn")
    @permission_level(SUPPORTER)
    @guild_only()
    async def warn(self, ctx: Context, member: Member, *, reason: str):
        """
        warn a member
        """

        try:
            await member.send(translations.f_warned(ctx.author.mention, ctx.guild.name, reason))
        except (Forbidden, HTTPException):
            await ctx.send(translations.no_dm)
        await run_in_thread(Warn.create, member.id, ctx.author.id, reason)
        await ctx.send(translations.warned_response)
        await send_to_changelog(ctx.guild, translations.f_log_warned(ctx.author.mention, member.mention, reason))