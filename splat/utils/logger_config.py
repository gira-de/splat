import logging
import sys

from splat.config.model import LogLevel
from splat.interface.logger import LoggerInterface

_DEFAULT_FORMAT = "[%(asctime)s] %(levelname)-5s -- %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S %z"


class RealLogger(LoggerInterface):
    def __init__(self, logger: logging.Logger | None = None, context: str = "splat") -> None:
        self._logger = logger or logging.getLogger("splat")
        self._context = context
        self.update_log_level(LogLevel.INFO)

    def update_context(self, new_context: str = "splat") -> None:
        self._context = new_context

    def _with_context(self, msg: str) -> str:
        return f"[{self._context}] {msg}"

    def info(self, msg: str) -> None:
        self._logger.info(self._with_context(msg))

    def debug(self, msg: str) -> None:
        self._logger.debug(self._with_context(msg))

    def warning(self, msg: str) -> None:
        self._logger.warning(self._with_context(msg))

    def error(self, msg: str) -> None:
        self._logger.error(self._with_context(msg))

    def update_log_level(self, log_level: LogLevel) -> None:
        self._logger.setLevel(log_level.value)
        _clear_handlers(self._logger)
        _add_console_handler(self._logger, log_level)


def _clear_handlers(target_logger: logging.Logger) -> None:
    while target_logger.handlers:
        target_logger.removeHandler(target_logger.handlers[0])


def _add_console_handler(target_logger: logging.Logger, log_level: LogLevel) -> None:
    formatter = logging.Formatter(_DEFAULT_FORMAT, datefmt=_DEFAULT_DATEFMT)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level.value)
    target_logger.addHandler(console_handler)
