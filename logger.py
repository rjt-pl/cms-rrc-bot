from __future__ import annotations
import logging
from logging import StreamHandler
import sys

from typing import (
    TYPE_CHECKING,
)
if TYPE_CHECKING:
    from typing import (
        Any,
    )
    from typing_extensions import (
        Self,
    )


class ColourFormatter(logging.Formatter):
    LEVEL_COLOURS: list[tuple[int, str]] = [
        (logging.DEBUG, '\x1b[40;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]
    FORMATS: dict[int, logging.Formatter] = {
        level: logging.Formatter(
            f'\x1b[0;1m[\x1b[30;1m%(asctime)s\x1b[0;1m] [\x1b[0m{colour}%(levelname)-7s\x1b[0;1m]\x1b[0m \x1b[35m%(name)s:\x1b[0m %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record: logging.LogRecord):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        if record.exc_info:  # Override the traceback to always print in red
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)
        record.exc_text = None  # Remove the cache layer
        return output


class SetupLogging:
    def __init__(self) -> None:
        self.log = logging.getLogger()

    def __enter__(self) -> Self:
        self.log.setLevel(logging.INFO)
        handlers: list[tuple[logging.Handler, logging.Formatter]] = [
            (
                StreamHandler(sys.stdout),
                ColourFormatter()
            )
        ]
        for handler, formatter in handlers:
            handler.setFormatter(formatter)
            self.log.addHandler(handler)
        return self

    def __exit__(self, *args: Any) -> None:
        handlers = self.log.handlers[:]
        for handler in handlers:
            handler.close()
            self.log.removeHandler(handler)
