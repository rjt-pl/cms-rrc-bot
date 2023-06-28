from __future__ import annotations
from discord.ext import commands

from utils import (
    text_admin_only,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bot import Bot


class Admin(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot

    # @commands.command(name='sync')
    # @text_admin_only()
    # async def sync(self, ctx: commands.Context) -> None:
    #     message = await ctx.send(embed=self.bot.embed('Syncing...'))
    #     await self.bot.tree.sync()
    #     await message.edit(embed=self.bot.embed('Successfully synced.'))

    @commands.command(name='reload')
    @text_admin_only()
    async def reload(self, ctx: commands.Context) -> None:
        await self.bot.load(re=True)
        await ctx.send(embed=self.bot.embed('Successfully reloaded.'))


async def setup(bot: Bot) -> None:
    await bot.add_cog(Admin(bot))
