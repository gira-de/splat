from splat.model import RemoteProject
from splat.source_control.github.GithubPlatform import GithubPlatform
from splat.source_control.github.model import GitHubConfig
from tests.mocks import MockEnvManager, MockGitHubAPI, MockLogger
from tests.source_control.base_test import BaseSourceControlTest


class BaseGithubSourceControlTest(BaseSourceControlTest):
    def setUp(self) -> None:
        super().setUp()
        self.mock_api = MockGitHubAPI(domain="https://github.com", access_token="secret_token")  # nosec
        self.mock_logger = MockLogger()
        self.mock_env_manager = MockEnvManager()
        self.github_platform = GithubPlatform(
            config=GitHubConfig(
                type="github",
                domain="https://github.com",
                access_token="secret_token",  # nosec
            ),
            logger=self.mock_logger,
            env_manager=self.mock_env_manager,
            api=self.mock_api,
        )

        self.project = RemoteProject(
            default_branch="main",
            id=1,
            name_with_namespace="group/repo",
            web_url="http://github.com/repo",
            clone_url="http://github.com/repo.git",
        )

    def setup_mock_requests_post(self) -> None:
        self.mock_api._post_request_response = {
            "title": "Splat Dependency Updates",
            "body": "Some body",
            "html_url": "http://github.com/pull/1",
            "url": "http://api.github.com/pulls/1",
            "head": {"ref": self.branch_name, "repo": {"html_url": "http://github.com/repo"}},
        }

    def setup_mock_requests_patch(self) -> None:
        self.mock_api._patch_request_response = {
            "title": "Splat Dependency Updates",
            "body": "Some updated body",
            "html_url": "http://github.com/pull/1",
            "url": "http://api.github.com/pulls/1",
            "head": {"ref": self.branch_name, "repo": {"html_url": "http://github.com/repo"}},
        }
