from splat.config.model import PlatformConfig
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.source_control.common.maintainer_finder import find_project_maintainer
from splat.utils.env_manager.interface import EnvManager
from tests.mocks.mock_env_manager import MockEnvManager
from tests.mocks.mock_logger import MockLogger


class MockGitPlatform(GitPlatformInterface):
    def __init__(
        self,
        config: PlatformConfig,
        projects: list[RemoteProject],
        open_merge_request_url: str | None = "",
        project_topics: dict[str, list[str]] | None = None,
    ) -> None:
        self._config = config
        self.logger = MockLogger()
        self.env_manager = MockEnvManager()
        self._id = "mock_id"
        self.projects = projects
        self.open_merge_request_url = open_merge_request_url
        self.project_topics = project_topics or {}

    @property
    def config(self) -> PlatformConfig:
        return self._config

    @property
    def type(self) -> str:
        return "mock"

    @property
    def id(self) -> str | None:
        return self._id

    @id.setter
    def id(self, value: str | None) -> None:
        self._id = value if value is not None else ""

    @property
    def name(self) -> str:
        return "mock_name"

    @property
    def domain(self) -> str:
        return "https://mock.example.com"

    @property
    def merge_request_type(self) -> str:
        return "pull_mock"

    @property
    def access_token(self) -> str:
        return "mock_token"

    @classmethod
    def from_platform_config(
        cls, platform_config: PlatformConfig, logger: LoggerInterface, env_manager: EnvManager
    ) -> GitPlatformInterface:
        return MockGitPlatform(PlatformConfig(type="mock"), [])

    def fetch_projects(self, project_id: str | None = None, timeout: float = 60.0) -> list[RemoteProject]:
        return self.projects

    def create_or_update_merge_request(
        self,
        project: RemoteProject,
        commit_messages: list[str],
        branch_name: str,
        remaining_vulns: list[AuditReport],
        title: str = "Splat Dependency Updates",
    ) -> MergeRequest:
        return MergeRequest(
            title, "url", "project_url", "project_name", self.merge_request_type, number=1, assignee=None
        )

    def get_open_merge_request_url(self, project: RemoteProject, branch_name: str, timeout: int = 10) -> str | None:
        return self.open_merge_request_url

    def get_project_topics(self, project: RemoteProject) -> list[str]:
        return self.project_topics.get(project.name_with_namespace, [])

    def get_maintainer(self, project: RemoteProject) -> str | None:
        topics = self.get_project_topics(project)
        return find_project_maintainer(project.name_with_namespace, topics, self.logger)
