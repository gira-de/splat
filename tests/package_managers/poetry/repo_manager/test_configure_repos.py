import unittest

from splat.config.model import RepoConfig, RepoCredentials
from splat.package_managers.poetry.repo_manager import PoetryRepoManager
from tests.package_managers.common.test_base_repo_manager import TestBasePipRepoManager


class TestConfigureRepositories(TestBasePipRepoManager):
    def setUp(self) -> None:
        super().setUp()
        self.repo_manager = PoetryRepoManager(self.env_manager, self.mock_fs, self.mock_logger)

    def _pip_conf_path(self) -> str:
        return str(self.mock_fs.home() / ".config" / "pip" / "pip.conf")

    def _netrc_path(self) -> str:
        return str(self.mock_fs.home() / ".netrc")

    def test_basic_http_auth_configuration(self) -> None:
        # Expected repo exists with HTTP basic credentials.
        expected_repos = {
            "repo1": RepoConfig(
                url="https://example.com/path/",
                credentials=RepoCredentials(username="user", password="pass"),  # nosec
            )
        }
        manifest_sources = {
            "repo1": "https://example.com/path"  # Normalized to match expected.
        }
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertTrue(self.mock_logger.has_logged("DEBUG: Setting HTTP basic authentication for repository 'repo1'."))
        self.assertEqual(self.env_manager.get("POETRY_HTTP_BASIC_REPO1_USERNAME"), "user")
        self.assertEqual(self.env_manager.get("POETRY_HTTP_BASIC_REPO1_PASSWORD"), "pass")
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        self.assertTrue(self.mock_fs.exists(self._netrc_path()))

    def test_token_auth_configuration(self) -> None:
        # Expected repo exists with token credentials.
        expected_repos = {
            "repo1": RepoConfig(url="https://example.com/path", credentials=RepoCredentials(token="abc123"))  # nosec
        }
        manifest_sources = {
            "repo1": "https://example.com/path/"  # Normalized equivalence.
        }
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertTrue(self.mock_logger.has_logged("DEBUG: Setting token authentication for repository 'repo1'."))
        self.assertEqual(self.env_manager.get("POETRY_PYPI_TOKEN_REPO1"), "abc123")
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        self.assertTrue(self.mock_fs.exists(self._netrc_path()))


if __name__ == "__main__":
    unittest.main()
