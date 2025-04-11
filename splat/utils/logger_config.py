import logging
import sys
from typing import TYPE_CHECKING, Any

from splat.config.model import LogLevel
from splat.interface.logger import LoggerInterface

if TYPE_CHECKING:
    _LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    _LoggerAdapter = logging.LoggerAdapter


# --- Real Logger Implementation ---
class ContextLoggerAdapter(_LoggerAdapter, LoggerInterface):
    def __init__(self, logger: logging.Logger, context: str):
        super().__init__(logger, {})
        self.context = context

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        return f"[{self.context}] {msg}", kwargs

    def update_context(self, new_context: str = "splat") -> None:
        self.context = new_context


class LoggerManager:
    def __init__(self, name: str):
        self.base_name = name
        self.default_format = "[%(asctime)s] %(levelname)-5s -- %(message)s"
        self.default_datefmt = "%Y-%m-%d %H:%M:%S %z"
        self.loggers: dict[str, ContextLoggerAdapter] = {}

    def setup_logger(self, plugin_name: str = "splat", log_level: LogLevel = LogLevel.INFO) -> ContextLoggerAdapter:
        logger = logging.getLogger(f"{self.base_name}.{plugin_name}")
        logger.setLevel(log_level.value)
        self._clear_handlers(logger)
        self._add_console_handler(logger, log_level)

        adapter = ContextLoggerAdapter(logger, plugin_name)
        self.loggers[plugin_name] = adapter
        return adapter

    def _clear_handlers(self, logger: logging.Logger) -> None:
        while logger.handlers:
            logger.removeHandler(logger.handlers[0])

    def _add_console_handler(self, logger: logging.Logger, log_level: LogLevel) -> None:
        formatter = logging.Formatter(self.default_format, datefmt=self.default_datefmt)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level.value)
        logger.addHandler(console_handler)

    def update_logger_level(self, log_level: LogLevel) -> None:
        for _, adapter in self.loggers.items():
            logger = adapter.logger
            logger.setLevel(log_level.value)
            self._clear_handlers(logger)
            self._add_console_handler(logger, log_level)

    def get_logger(self, plugin_name: str = "splat") -> ContextLoggerAdapter:
        if plugin_name not in self.loggers:
            return self.setup_logger(plugin_name)
        return self.loggers[plugin_name]


logger_manager = LoggerManager("Splat-logger")

# Initial setup
logger = logger_manager.setup_logger()  # TODO: replace usage by default_logger
default_logger: LoggerInterface = logger_manager.get_logger("splat")
