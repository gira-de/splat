from abc import ABC, abstractmethod

from splat.config.model import Config
from splat.interface.GitPlatformInterface import GitPlatformInterface


# Abstract base class for Execution Environments
class ExecutionEnvironmentInterface(ABC):
    def __init__(self, config: Config, git_platforms: list[GitPlatformInterface]) -> None:
        self.config = config
        self.git_platforms = git_platforms

    @abstractmethod
    def execute(self) -> None:
        pass
