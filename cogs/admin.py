# admin.py - Admin commands for the bot
#
# These commands can only be run by people listed as owners in the bot's
# configuration.
#
# 2023 Ryan Thompson <i@ry.ca>

from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from main import config

from utils import (
    text_admin_only,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bot import Bot


class Admin(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: Bot = bot

    # Check if the user has the admin_role
    def can_run_command():
        def predicate(inter : discord.Interaction):
            role = discord.utils.find(
                lambda r: r.name == config['admin_role'], inter.guild.roles
            )
            if role in inter.user.roles:
                return True
        return app_commands.check(predicate)

    @app_commands.command(
        name        = 'reload',
        description = 'Reloads the RRC bot.',
    )
    @can_run_command()
    async def reload(self, inter: discord.Interaction) -> None:
        await self.bot.load(re=True)
        await ctx.send(embed=self.bot.embed('Successfully reloaded.'))


    @app_commands.command(
        name        = 'sendbutton',
        description = 'Sends the IRR submit button to the current channel.',
    )
    #@app_commands.check(can_run_command)
    @can_run_command()
    async def sendbutton(self, inter: discord.Interaction) -> None:
        view = discord.ui.View(timeout=0.01)
        emoji = await inter.guild.fetch_emoji(config['protest_emoji_id'])
        view.add_item(discord.ui.Button(
            label='File a Protest (IRR)',
            style=discord.ButtonStyle.blurple,
            custom_id='questions:::start',
            emoji=emoji
        ))
        embed = self.bot.embed(config['button_message'])
        await inter.response.send_message(embed=embed, view=view)


    # Prints out a list of all tags for the configured forum.
    # Use these to set up the tag logic
    @app_commands.command(
        name        = "forumtags",
        description = "Display a list of all tags in the configured forum.",
    )
    @can_run_command()
    async def forumtags(self, inter: discord.Interaction) -> None:
        forum = inter.guild.get_channel(config['forum_channel_id'])
        embed = self.bot.embed(
            title='Forum Tags',
            description='\n'.join(
                f'ID: `{tag.id}` ' \
                f'{(str(tag.emoji) + " ") if tag.emoji else ""}**{tag.name}**' \
                for tag in forum.available_tags) or 'No tags found.',
        )
        await inter.response.send_message(embed=embed)

    # TODO refactor

    @sendbutton.error
    async def sendbutton_error(self, inter: discord.Interaction, error):
        await inter.response.send_message(
            "You do not have permission to run the `/sendbutton` command.",
            ephemeral=True
        )

    @forumtags.error
    async def forumtags_error(self, inter: discord.Interaction, error):
        await inter.response.send_message(
            "You do not have permission to run the `/forumtags` command.",
            ephemeral=True
        )

    @reload.error
    async def reload_cmd_error(self, inter: discord.Interaction, error):
        await inter.response.send_message(
            "You do not have permission to run the `/reload` command.",
            ephemeral=True
        )

async def setup(bot: Bot) -> None:
    await bot.add_cog(Admin(bot))
