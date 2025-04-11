from unittest.mock import MagicMock

from splat.model import RemoteProject
from splat.source_control.github.api import GitHubAPI
from splat.source_control.github.GithubPlatform import GithubPlatform
from splat.source_control.github.model import GitHubConfig
from tests.mocks import MockLogger
from tests.source_control.base_test import BaseSourceControlTest


class BaseGithubSourceControlTest(BaseSourceControlTest):
    def setUp(self) -> None:
        super().setUp()
        self.mock_api = MagicMock(spec=GitHubAPI)
        self.mock_api.api_base_url = "https://api.github.com"
        self.mock_api.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer secret_token",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.mock_logger = MockLogger()
        self.github_platform = GithubPlatform(
            config=GitHubConfig(
                type="github",
                domain="https://github.com",
                access_token="secret_token",  # nosec
            ),
            logger=self.mock_logger,
        )
        self.github_platform.api = self.mock_api

        self.project = RemoteProject(
            default_branch="main",
            id=1,
            name_with_namespace="group/repo",
            web_url="http://github.com/repo",
            clone_url="http://github.com/repo.git",
        )

    def setup_mock_requests_post(self, mock_post: MagicMock) -> None:
        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {
            "title": "Splat Dependency Updates",
            "body": "Some body",
            "html_url": "http://github.com/pull/1",
            "url": "http://api.github.com/pulls/1",
            "head": {"repo": {"html_url": "http://github.com/repo"}},
        }
        mock_post.return_value = mock_post_response

    def setup_mock_requests_patch(self, mock_patch: MagicMock) -> None:
        mock_patch_response = MagicMock()
        mock_patch_response.status_code = 200
        mock_patch_response.json.return_value = {
            "title": "Splat Dependency Updates",
            "body": "Some updated body",
            "html_url": "http://github.com/pull/1",
            "url": "http://api.github.com/pulls/1",
            "repo": {"html_url": "http://github.com/repo"},
        }
        mock_patch.return_value = mock_patch_response
