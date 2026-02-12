from abc import ABC, abstractmethod

from splat.config.model import Config
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.model import RuntimeContext


# Abstract base class for Execution Environments
class ExecutionEnvironmentInterface(ABC):
    def __init__(self, config: Config, git_platforms: list[GitPlatformInterface], ctx: RuntimeContext) -> None:
        self.config = config
        self.git_platforms = git_platforms
        self.ctx = ctx
        self.logger = ctx.logger
        self.env_manager = ctx.env_manager

    @abstractmethod
    def execute(self) -> None:
        pass
