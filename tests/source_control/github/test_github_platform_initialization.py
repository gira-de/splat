import unittest

from splat.config.model import FiltersConfig
from splat.source_control.common.description_generator import DescriptionGenerator
from splat.source_control.github.GithubPlatform import GithubPlatform
from splat.source_control.github.model import GitHubConfig
from tests.mocks import MockLogger
from tests.mocks.mock_env_manager import MockEnvManager


class TestGithubPlatformInitialization(unittest.TestCase):
    def setUp(self) -> None:
        self.expected_headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer mock_access_token",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def test_github_platform_initialization(self) -> None:
        mock_env_manager = MockEnvManager()
        mock_logger = MockLogger()
        mock_env_manager.set("https://github.com", "https://github.com")
        mock_env_manager.set("TOKEN", "mock_access_token")
        github_platform = GithubPlatform(
            config=GitHubConfig(
                type="github",
                domain="https://github.com",
                access_token="$TOKEN",
                filters=FiltersConfig(),
            ),  # nosec
            logger=mock_logger,
            env_manager=mock_env_manager,
        )

        self.assertEqual("https://github.com", mock_env_manager.get("https://github.com"))
        self.assertEqual("mock_access_token", mock_env_manager.get("TOKEN"))

        self.assertEqual(github_platform.api.api_base_url, "https://api.github.com")

        self.assertIsInstance(github_platform.filters, FiltersConfig)

        self.assertEqual(github_platform.api.headers, self.expected_headers)

        self.assertIsInstance(github_platform.description_generator, DescriptionGenerator)

        self.assertIs(github_platform.pr_handler.api, github_platform.api)
        self.assertIs(github_platform.pr_handler.logger, mock_logger)

    def test_github_platform_initialization_with_custom_domain(self) -> None:
        mock_logger = MockLogger()
        mock_env_manager = MockEnvManager()
        platform = GithubPlatform(
            GitHubConfig(
                type="github",
                domain="https://custom.github.com",
                access_token="mock_access_token",
            ),  # nosec
            logger=mock_logger,
            env_manager=mock_env_manager,
        )

        self.assertEqual(platform.api.api_base_url, "https://custom.github.com/api/v3")

        expected_headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer mock_access_token",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.assertEqual(platform.api.headers, expected_headers)


if __name__ == "__main__":
    unittest.main()
