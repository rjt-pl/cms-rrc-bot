from __future__ import annotations
from discord.ext import commands
from discord import app_commands
import discord

from utils import (
    Color,
)

import aiohttp

import logging

from typing import (
    TYPE_CHECKING,
)
if TYPE_CHECKING:
    from typing import (
        Optional,
    )
    from typing_extensions import (
        Self,
    )


log = logging.getLogger(__name__)


class Bot(commands.Bot):
    user: discord.User
    session: aiohttp.ClientSession
    cog_names: tuple[str, ...]
    def __init__(
        self,
        owner_ids: list[int],
    ) -> None:
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.cog_names: tuple[str, ...] = (
            'cogs.admin',
            'cogs.questionnaire',
        )
        super().__init__(
            command_prefix=self.get_prefixes,
            activity=discord.Activity(type=discord.ActivityType.listening, name='you'),
            status=discord.Status.online,
            help_command=None,
            strip_after_prefix=True,
            intents=discord.Intents.all(),
            case_insensitive=True,
            owner_ids=set(owner_ids),
        )
        self.tree.on_error = self.on_app_command_error

    def get_prefixes(self, bot: commands.Bot, message: discord.Message) -> list[str]:
        return ['!']

    async def load(self, re: bool = False) -> None:
        func = self.reload_extension if re else self.load_extension
        for cog_name in self.cog_names:
            await func(cog_name)
        log.info('Cogs (re)loaded')

    async def setup_hook(self) -> None:
        await self.load()
        self.app_info = self.application or await self.application_info()
        self.owner: discord.User = self.app_info.owner
        log.info(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_command_error(self, ctx: commands.Context[Self], error: Exception) -> None:
        if isinstance(error, commands.CheckFailure):
            return
        raise error

    async def on_app_command_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if isinstance(error, app_commands.CheckFailure):
            return
        raise error

    def embed(self, description: Optional[str] = None, title: Optional[str] = None, color: Optional[int] = None) -> discord.Embed:
        if title is not None:
            if not (title.startswith('**') and title.endswith('**')):
                title = f'**{title}**'
        return discord.Embed(
            title=title,
            description=description,
            color=color or Color.regular,
        )
