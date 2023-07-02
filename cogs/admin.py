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

    @app_commands.command(
        name        = 'reload',
        description = 'Reloads the RRC bot.',
    )
    async def reload(self, inter: discord.Interaction) -> None:
        await self.bot.load(re=True)
        await ctx.send(embed=self.bot.embed('Successfully reloaded.'))


    @app_commands.command(
        name        = 'sendbutton',
        description = 'Sends the IRR submit button to the current channel.',
    )
    async def send_button(self, inter: discord.Interaction) -> None:
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
    async def forum_tags(self, inter: discord.Interaction) -> None:
        forum = inter.guild.get_channel(config['forum_channel_id'])
        embed = self.bot.embed(
            title='Forum Tags',
            description='\n'.join(
                f'ID: `{tag.id}` ' \
                f'{(str(tag.emoji) + " ") if tag.emoji else ""}**{tag.name}**' \
                for tag in forum.available_tags) or 'No tags found.',
        )
        await inter.response.send_message(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Admin(bot))
