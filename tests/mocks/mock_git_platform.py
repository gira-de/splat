from typing import Optional

from splat.config.model import PlatformConfig
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.model import AuditReport, MergeRequest, RemoteProject


class MockGitPlatform(GitPlatformInterface):
    def __init__(self, config: PlatformConfig, projects: list[RemoteProject]) -> None:
        super().__init__(config)
        self._id = "mock_id"
        self.projects = projects

    @property
    def type(self) -> str:
        return "mock"

    @property
    def id(self) -> Optional[str]:
        return self._id

    @id.setter
    def id(self, value: Optional[str]) -> None:
        self._id = value if value is not None else ""

    @property
    def name(self) -> str:
        return "mock_name"

    @property
    def merge_request_type(self) -> str:
        return "pull_mock"

    @property
    def access_token(self) -> str:
        return "mock_token"

    @classmethod
    def from_platform_config(cls, platform_config: PlatformConfig) -> GitPlatformInterface:
        return MockGitPlatform(PlatformConfig(type="mock"), [])

    def fetch_projects(self, project_id: Optional[str] = None, timeout: float = 60.0) -> list[RemoteProject]:
        return self.projects

    def create_or_update_merge_request(
        self,
        project: RemoteProject,
        commit_messages: list[str],
        branch_name: str,
        remaining_vulns: list[AuditReport],
        title: str = "Splat Dependency Updates",
    ) -> MergeRequest:
        return MergeRequest(title, "url", "project_url", "project_name", self.merge_request_type)
