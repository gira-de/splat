from abc import ABC, abstractmethod

from splat.interface.logger import LoggerInterface
from splat.utils.logger_config import default_logger


class EnvManager(ABC):
    """Abstract interface for managing environment variables."""

    def __init__(self, logger: LoggerInterface = default_logger) -> None:
        self.logger = logger

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> str:
        pass

    def resolve_value(self, value: str) -> str:
        """
        If the value starts with a '$', treat it as an environment variable reference
        and return its value; otherwise, return the original value.
        """
        if value.startswith("$"):
            # Remove the '$' and any surrounding braces (e.g. "$VAR" or "${VAR}")
            env_var = value.lstrip("$").strip("{}")
            return self.get(env_var)

        return value
