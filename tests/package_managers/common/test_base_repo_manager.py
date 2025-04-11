import unittest

from splat.config.model import RepoConfig, RepoCredentials
from splat.package_managers.common.base_repo_manager import BasePipRepoManager
from tests.mocks import MockEnvManager, MockFileSystem, MockLogger


class TestBasePipRepoManager(unittest.TestCase):
    def setUp(self) -> None:
        self.env_manager = MockEnvManager()
        self.mock_logger = MockLogger()
        self.mock_fs = MockFileSystem()
        self.repo_manager = BasePipRepoManager(self.env_manager, self.mock_fs, self.mock_logger)
        self._set_credentials()

    def _pip_conf_path(self) -> str:
        return str(self.mock_fs.home() / ".config" / "pip" / "pip.conf")

    def _netrc_path(self) -> str:
        return str(self.mock_fs.home() / ".netrc")

    def _set_credentials(self) -> None:
        # To silence bandit warnings
        self.env_manager.set("PASS", "pass")
        self.env_manager.set("TOKEN", "token")

    def test_missing_repo_in_manifest(self) -> None:
        expected_repos = {"repo1": RepoConfig(url="https://example.com/repo", credentials=None)}
        manifest_sources: dict[str, str] = {}  # repo1 is missing
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertFalse(self.mock_fs.exists(self._pip_conf_path()))
        self.assertFalse(self.mock_fs.exists(self._netrc_path()))
        self.assertTrue(self.mock_logger.has_logged("Repository 'repo1' mismatch or not found"))

    def test_url_mismatch(self) -> None:
        expected_repos = {"repo1": RepoConfig(url="https://example.com/repo", credentials=None)}
        manifest_sources = {"repo1": "https://different.com/repo"}
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertFalse(self.mock_fs.exists(self._pip_conf_path()))
        self.assertFalse(self.mock_fs.exists(self._netrc_path()))
        self.assertTrue(self.mock_logger.has_logged("Repository 'repo1' mismatch or not found"))

    def test_valid_basic_auth(self) -> None:
        ps = self.env_manager.get("PASS")
        creds = RepoCredentials(username="username", password=ps)
        expected_repos = {"repo1": RepoConfig(url="https://example.com/repo", credentials=creds)}
        manifest_sources = {"repo1": "https://example.com/repo"}
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        self.assertTrue(self.mock_fs.exists(self._netrc_path()))
        self.assertTrue(self.mock_logger.has_logged("DEBUG: Setting HTTP basic authentication"))

    def test_valid_token_auth(self) -> None:
        tk = self.env_manager.get("TOKEN")
        creds = RepoCredentials(token=tk)
        expected_repos = {"repo1": RepoConfig(url="https://example.com/repo", credentials=creds)}
        manifest_sources = {"repo1": "https://example.com/repo"}
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        self.assertTrue(self.mock_fs.exists(self._netrc_path()))
        self.assertTrue(self.mock_logger.has_logged("DEBUG: Setting token authentication"))

    def test_incomplete_basic_auth(self) -> None:
        creds = RepoCredentials(username="user", password=None)
        expected_repos = {"repo1": RepoConfig(url="https://example.com/repo", credentials=creds)}
        manifest_sources = {"repo1": "https://example.com/repo"}
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        self.assertFalse(self.mock_fs.exists(self._netrc_path()))
        self.assertTrue(
            self.mock_logger.has_logged(
                "DEBUG: No valid credentials provided for repository 'repo1', skipping authentication."
            )
        )

    def test_incomplete_token(self) -> None:
        creds = RepoCredentials(token=None)
        expected_repos = {"repo1": RepoConfig(url="https://example.com/repo", credentials=creds)}
        manifest_sources = {"repo1": "https://example.com/repo"}
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        self.assertFalse(self.mock_fs.exists(self._netrc_path()))
        self.assertTrue(
            self.mock_logger.has_logged(
                "DEBUG: No valid credentials provided for repository 'repo1', skipping authentication."
            )
        )

    def test_no_credentials(self) -> None:
        expected_repos = {"repo1": RepoConfig(url="https://example.com/repo", credentials=None)}
        manifest_sources = {"repo1": "https://example.com/repo"}
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        self.assertFalse(self.mock_fs.exists(self._netrc_path()))
        self.assertTrue(
            self.mock_logger.has_logged(
                "DEBUG: No credentials provided for repository 'repo1', skipping authentication."
            )
        )

    def test_multiple_repos_of_multiple_machines(self) -> None:
        ps = self.env_manager.get("PASS")
        tk = self.env_manager.get("TOKEN")
        repos = {
            "repo1": RepoConfig(
                url="https://example.com/repo1", credentials=RepoCredentials(username="user", password=ps)
            ),
            "repo2": RepoConfig(url="https://example2.com/repo2", credentials=RepoCredentials(token=tk)),
        }
        manifest = {
            "repo1": "https://example.com/repo1",
            "repo2": "https://example2.com/repo2",
        }
        self.repo_manager.configure_repositories(repos, manifest)
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        netrc = self._netrc_path()
        if self.mock_fs.exists(netrc):
            netrc_content = self.mock_fs.read(netrc)
            self.assertIn("login user", netrc_content)
            self.assertIn("password pass", netrc_content)
            self.assertIn("login __token__", netrc_content)
            self.assertIn("password token", netrc_content)

    def test_multiple_repos_some_invalid_creds(self) -> None:
        tk = self.env_manager.get("TOKEN")
        repos = {
            "repo1": RepoConfig(
                url="https://example.com/repo1",
                credentials=RepoCredentials(username="user", password=None),  # Password missing, invalid
            ),
            "repo2": RepoConfig(url="https://example2.com/repo2", credentials=RepoCredentials(token=tk)),
        }
        manifest = {
            "repo1": "https://example.com/repo1",
            "repo2": "https://example2.com/repo2",
        }
        self.repo_manager.configure_repositories(repos, manifest)
        self.assertTrue(self.mock_fs.exists(self._pip_conf_path()))
        netrc = self._netrc_path()
        if self.mock_fs.exists(netrc):
            netrc_content = self.mock_fs.read(netrc)
            # only those repos with valid credentials are included
            self.assertIn("login __token__", netrc_content)
            self.assertIn("password token", netrc_content)

    def test_empty_expected_repos(self) -> None:
        expected_repos: dict[str, RepoConfig] = {}
        manifest_sources = {"any": "https://example.com"}
        self.repo_manager.configure_repositories(expected_repos, manifest_sources)
        self.assertFalse(self.mock_fs.exists(self._pip_conf_path()))
        self.assertFalse(self.mock_fs.exists(self._netrc_path()))


if __name__ == "__main__":
    unittest.main()
