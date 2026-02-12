from __future__ import annotations

from abc import ABC, abstractmethod

from splat.config.model import PlatformConfig
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.utils.env_manager.interface import EnvManager


class GitPlatformInterface(ABC):
    def __init__(self, config: PlatformConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def type(self) -> str:
        """Platform type like 'gitlab' or 'github'."""
        pass

    @property
    def id(self) -> str | None:
        return self.config.id

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the platform, optional, used for logging"""
        pass

    @property
    @abstractmethod
    def merge_request_type(self) -> str:
        pass

    @property
    @abstractmethod
    def access_token(self) -> str:
        """The value of environment variable of the access token"""
        pass

    @classmethod
    @abstractmethod
    def from_platform_config(
        cls, platform_config: PlatformConfig, logger: LoggerInterface, env_manager: EnvManager
    ) -> GitPlatformInterface:
        pass

    @abstractmethod
    def fetch_projects(self, project_id: str | None = None, timeout: float = 60.0) -> list[RemoteProject]:
        pass

    @abstractmethod
    def get_open_merge_request_url(self, project: RemoteProject, branch_name: str) -> str | None:
        """Return an open MR/PR for the branch (or title) if it exists."""
        pass

    @abstractmethod
    def create_or_update_merge_request(
        self,
        project: RemoteProject,
        commit_messages: list[str],
        branch_name: str,
        remaining_vulns: list[AuditReport],
        title: str = "Splat Dependency Updates",
    ) -> MergeRequest:
        pass
