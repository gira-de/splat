# --- Logger Interface ---
from abc import ABC, abstractmethod


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
