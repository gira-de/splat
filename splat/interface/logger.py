# --- Logger Interface ---
from abc import ABC, abstractmethod

from splat.config.model import LogLevel


class LoggerInterface(ABC):
    @abstractmethod
    def info(self, msg: str) -> None:
        pass

    @abstractmethod
    def debug(self, msg: str) -> None:
        pass

    @abstractmethod
    def warning(self, msg: str) -> None:
        pass

    @abstractmethod
    def error(self, msg: str) -> None:
        pass

    @abstractmethod
    def update_context(self, new_context: str = "splat") -> None:
        pass

    @abstractmethod
    def update_log_level(self, log_level: LogLevel) -> None:
        pass
