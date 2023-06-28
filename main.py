#!/usr/bin/env python3

from __future__ import annotations
from bot import Bot

import asyncio
import json

from logger import SetupLogging
import logging

from typing import (
    TYPE_CHECKING,
)
if TYPE_CHECKING:
    from typing import (
        NotRequired,
        TypedDict,
        Literal,
    )

    class _Config(TypedDict):
        token: str
        owner_ids: list[int]
        guild_id: int
        log_channel_id: int
        forum_channel_id: int


log = logging.getLogger(__name__)


with open('config/config.json', 'r', encoding='utf-8') as file:
    config: _Config = json.load(file)


async def start() -> None:
    bot = Bot(
        owner_ids=config.get('owner_ids'),
    )
    await bot.start(config.get('token'))


def main() -> None:
    with SetupLogging():
        asyncio.run(start())


if __name__ == '__main__':
    main()
