from splat.model import RemoteProject
from splat.source_control.gitlab.GitlabPlatform import GitlabPlatform
from splat.source_control.gitlab.model import GitLabConfig
from tests.mocks import MockEnvManager, MockGitLabAPI, MockLogger
from tests.source_control.base_test import BaseSourceControlTest


class BaseGitlabSourceControlTest(BaseSourceControlTest):
    def setUp(self) -> None:
        super().setUp()
        self.base_url = "http://gitlab.com"
        self.config = GitLabConfig(type="gitlab", domain=self.base_url, access_token="access")  # nosec
        self.fake_logger = MockLogger()
        self.fake_env_manager = MockEnvManager()
        self.fake_api = MockGitLabAPI(self.base_url)
        self.gitlab_platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, self.fake_api)

        self.project = RemoteProject(
            default_branch="main",
            id=1,
            name_with_namespace="group/project",
            web_url="http://gitlab.com/project",
            clone_url="http://gitlab.com/project.git",
        )
