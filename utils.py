from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands

import asyncio
import json
import os

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bot import Bot
    from typing import (
        ParamSpec,
        Awaitable,
        Iterator,
        Callable,
        Optional,
        Generic,
        TypeVar,
        Any,
    )

    _T = TypeVar('_T')
    _D = TypeVar('_D')

    ObjectHook = Callable[[dict[str, Any]], Any]

    P = ParamSpec('P')
    Command = Callable[P, Awaitable[None]]
else:
    Generic = (object,)
    _T = 0
    _D = 0


__all__ = (
    'ConfigArray',
    'Config',
    'Color',
    'is_admin',
    'non_admin_embed',
    'hybrid_admin_only',
    'text_admin_only',
    'application_admin_only',
)


class ConfigArray(Generic[_T]):
    def __init__(self, name: str, object_hook: Optional[ObjectHook] = None, encoder: Optional[type[json.JSONEncoder]] = None) -> None:
        self.name = name
        self.path = './' + name
        self.object_hook = object_hook
        self.encoder = encoder
        self.loop = asyncio.get_running_loop()
        self.lock = asyncio.Lock()
        self._db: list[_T] = []
        self.load_from_file()

    def load_from_file(self) -> None:
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self._db = json.load(f, object_hook=self.object_hook)
        except FileNotFoundError:
            self._db = []

    async def load(self) -> None:
        async with self.lock:
            await self.loop.run_in_executor(None, self.load_from_file)

    def _dump(self) -> None:
        temp = self.path + f'{os.urandom(16).hex()}.tmp'
        with open(temp, 'w', encoding='utf-8') as tmp:
            json.dump(self._db.copy(), tmp, ensure_ascii=True,
                      cls=self.encoder, separators=(',', ':'))

        # atomically move the file
        os.replace(temp, self.path)

    async def save(self) -> None:
        async with self.lock:
            await self.loop.run_in_executor(None, self._dump)

    async def add(self, item: _T) -> None:
        self._db.append(item)
        await self.save()

    async def remove(self, item: _T) -> None:
        self._db.remove(item)
        await self.save()

    def __contains__(self, item: Any) -> bool:
        return item in self._db

    def __len__(self) -> int:
        return len(self._db)

    def __iter__(self) -> Iterator[_T]:
        return iter(self._db)

    def all(self) -> list[_T]:
        return self._db

    def __str__(self) -> str:
        return str(self.all())


class Config(Generic[_T]):
    def __init__(self, name: str, object_hook: Optional[ObjectHook] = None, encoder: Optional[type[json.JSONEncoder]] = None) -> None:
        self.name = name
        self.path = './' + name
        self.object_hook = object_hook
        self.encoder = encoder
        self.loop = asyncio.get_running_loop()
        self.lock = asyncio.Lock()
        self._db: dict[str, _T] = {}
        self.load_from_file()

    def load_from_file(self) -> None:
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self._db = json.load(f, object_hook=self.object_hook)
        except FileNotFoundError:
            self._db = {}

    async def load(self) -> None:
        async with self.lock:
            await self.loop.run_in_executor(None, self.load_from_file)

    def _dump(self) -> None:
        temp = self.path + f'{os.urandom(16).hex()}.tmp'
        with open(temp, 'w', encoding='utf-8') as tmp:
            json.dump(self._db.copy(), tmp, ensure_ascii=True,
                      cls=self.encoder, separators=(',', ':'))

        # atomically move the file
        os.replace(temp, self.path)

    async def save(self) -> None:
        async with self.lock:
            await self.loop.run_in_executor(None, self._dump)

    def get(self, key: Any, default: _D = None) -> _T | _D:
        """Retrieves a config entry."""
        return self._db.get(str(key), default)

    async def put(self, key: Any, value: _T) -> None:
        """Edits a config entry."""
        self._db[str(key)] = value
        await self.save()

    async def remove(self, key: Any) -> None:
        """Removes a config entry."""
        del self._db[str(key)]
        await self.save()

    def __contains__(self, item: Any) -> bool:
        return str(item) in self._db

    def __getitem__(self, item: Any) -> _T:
        return self._db[str(item)]

    def __len__(self) -> int:
        return len(self._db)

    def all(self) -> dict[str, _T]:
        return self._db

    def __str__(self) -> str:
        return str(self.all())


class Color:
    regular = int(discord.Color.blue())
    error = int(discord.Color.red())


def is_admin(id: int, bot: Bot) -> bool:
    if TYPE_CHECKING:
        assert bot.owner_ids is not None
    return id in bot.owner_ids


def non_admin_embed(bot: Bot) -> discord.Embed:
    return bot.embed('You do not have permission to use this command.', color=Color.error)


def hybrid_admin_only(send_text: bool = False, send_app: bool = True):
    async def predicate(ctx: commands.Context[Bot]) -> bool:
        bot: Bot = ctx.bot
        if not is_admin(id=ctx.author.id, bot=bot):
            is_app = ctx.interaction is not None
            if (
                (is_app and send_app) or
                (not is_app and send_text)
            ):
                if TYPE_CHECKING:
                    assert ctx.interaction is not None
                send = ctx.send if not is_app else ctx.interaction.response.send_message
                await send(embed=non_admin_embed(bot=bot), ephemeral=True)
            raise commands.CheckFailure()
        return True
    return commands.check(predicate)


def text_admin_only(send: bool = False):
    async def predicate(ctx: commands.Context[Bot]) -> bool:
        bot: Bot = ctx.bot
        if not is_admin(id=ctx.author.id, bot=bot):
            if send:
                await ctx.send(embed=non_admin_embed(bot=bot))
            raise commands.CheckFailure()
        return True
    return commands.check(predicate)


def application_admin_only(send: bool = True):
    async def predicate(interaction: discord.Interaction) -> bool:
        if TYPE_CHECKING:
            assert isinstance(interaction.client, Bot)
        bot: Bot = interaction.client
        if not is_admin(id=interaction.user.id, bot=bot):
            if send:
                await interaction.response.send_message(embed=non_admin_embed(bot=bot), ephemeral=True)
            raise app_commands.CheckFailure()
        return True
    return app_commands.check(predicate)
