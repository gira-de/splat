import unittest
from unittest.mock import MagicMock

from splat.config.config_merger import _merge_package_managers_config
from splat.config.model import LocalPackageManagersConfig, PMConfig, RepoConfig
from splat.model import RuntimeContext
from splat.package_managers.pipenv.PipenvPackageManager import PipenvPackageManager
from splat.package_managers.poetry.PoetryPackageManager import PoetryPackageManager
from splat.package_managers.yarn.YarnPackageManager import YarnPackageManager
from tests.mocks import MockCommandRunner, MockEnvManager, MockFileSystem, MockLogger


class TestMergePackageManagersConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_runner = MockCommandRunner()
        mock_config = MagicMock(spec=PMConfig)
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.mock_env_manager = MockEnvManager()
        self.mock_ctx = RuntimeContext(
            logger=self.mock_logger,
            fs=self.mock_fs,
            command_runner=self.mock_runner,
            env_manager=self.mock_env_manager,
        )
        # Mock global package managers
        self.pipenv = PipenvPackageManager(mock_config, self.mock_ctx)
        self.yarn = YarnPackageManager(mock_config, self.mock_ctx)
        self.poetry = PoetryPackageManager(mock_config, self.mock_ctx)

        self.global_package_managers = [self.pipenv, self.yarn]

    def test_merge_package_manager_config_enables_new_package_manager_in_local(self) -> None:
        local_pm_config = LocalPackageManagersConfig(poetry=PMConfig(enabled=True))
        final_package_managers = _merge_package_managers_config(
            self.global_package_managers, local_pm_config, self.mock_ctx
        )
        self.assertEqual(len(final_package_managers), 3)
        self.assertIn(self.pipenv, final_package_managers)
        self.assertIn(self.yarn, final_package_managers)
        self.assertTrue(any(isinstance(pm, PoetryPackageManager) for pm in final_package_managers))
        self.assertTrue(
            self.mock_logger.has_logged("INFO: Configured package managers: 1 enabled, 0 disabled (poetry: Enabled)")
        )

    def test_merge_package_manager_config_disables_existing_package_manager_in_local(self) -> None:
        local_pm_config = LocalPackageManagersConfig(yarn=PMConfig(enabled=False))
        final_package_managers = _merge_package_managers_config(
            self.global_package_managers, local_pm_config, self.mock_ctx
        )
        self.assertEqual(len(final_package_managers), 1)
        self.assertIn(self.pipenv, final_package_managers)
        self.assertNotIn(self.yarn, final_package_managers)

    def test_merge_package_manager_config_no_change_to_package_managers(self) -> None:
        local_pm_config = LocalPackageManagersConfig()
        final_package_managers = _merge_package_managers_config(
            self.global_package_managers, local_pm_config, self.mock_ctx
        )
        self.assertEqual(len(final_package_managers), 2)
        self.assertIn(self.pipenv, final_package_managers)
        self.assertIn(self.yarn, final_package_managers)

    def test_merge_package_manager_config_enables_and_disables_package_managers(self) -> None:
        local_pm_config = LocalPackageManagersConfig(poetry=PMConfig(enabled=True), yarn=PMConfig(enabled=False))
        final_package_managers = _merge_package_managers_config(
            self.global_package_managers, local_pm_config, self.mock_ctx
        )
        self.assertEqual(len(final_package_managers), 2)
        self.assertIn(self.pipenv, final_package_managers)
        self.assertTrue(any(isinstance(pm, PoetryPackageManager) for pm in final_package_managers))
        self.assertNotIn(self.yarn, final_package_managers)
        self.assertTrue(
            self.mock_logger.has_logged("INFO: Configured package managers: 1 enabled, 0 disabled (poetry: Enabled)")
        )

    def test_merge_package_manager_config_local_config_is_none(self) -> None:
        final_package_managers = _merge_package_managers_config(self.global_package_managers, None, self.mock_ctx)
        self.assertEqual(len(final_package_managers), 2)
        self.assertIn(self.pipenv, final_package_managers)
        self.assertIn(self.yarn, final_package_managers)

    # --- Repository Merging Tests ---
    def test_merge_repositories_for_existing_pm(self) -> None:
        # global PMConfig for pipenv with a repository.
        global_repo_config = PMConfig(enabled=True, repositories={"repo1": RepoConfig(url="https://global-repo1.com")})
        pipenv_pm = PipenvPackageManager(global_repo_config, self.mock_ctx)
        # no repos for yarn
        global_yarn_config = PMConfig(enabled=True, repositories={})
        yarn_pm = YarnPackageManager(global_yarn_config, self.mock_ctx)
        global_pms = [pipenv_pm, yarn_pm]

        # Local config for pipenv: override repo1 and add repo2.
        local_pm_config = LocalPackageManagersConfig(
            pipenv=PMConfig(
                enabled=True,
                repositories={
                    "repo1": RepoConfig(url="https://local-repo1.com"),  # Overrides global
                    "repo2": RepoConfig(url="https://local-repo2.com"),  # New repository
                },
            )
        )

        final_package_managers = _merge_package_managers_config(global_pms, local_pm_config, self.mock_ctx)
        merged_pm_dict = {pm.name.lower(): pm for pm in final_package_managers}
        self.assertIn("pipenv", merged_pm_dict)
        merged_pipenv = merged_pm_dict["pipenv"]
        expected_repos = {
            "repo1": "https://local-repo1.com",  # local override
            "repo2": "https://local-repo2.com",
        }
        actual_repos = {key: repo.url for key, repo in merged_pipenv.config.repositories.items()}
        self.assertEqual(expected_repos, actual_repos)

    def test_merge_repositories_for_new_pm(self) -> None:
        # Global config does not include poetry.
        global_pm_config = PMConfig(enabled=True, repositories={})
        pipenv_pm = PipenvPackageManager(global_pm_config, self.mock_ctx)
        yarn_pm = YarnPackageManager(global_pm_config, self.mock_ctx)
        global_pms = [pipenv_pm, yarn_pm]

        # Local config enabling poetry with repository settings.
        local_pm_config = LocalPackageManagersConfig(
            poetry=PMConfig(enabled=True, repositories={"repo3": RepoConfig(url="https://local-repo3.com")})
        )

        final_package_managers = _merge_package_managers_config(global_pms, local_pm_config, self.mock_ctx)
        merged_pm_dict = {pm.name.lower(): pm for pm in final_package_managers}
        self.assertIn("poetry", merged_pm_dict)
        merged_poetry = merged_pm_dict["poetry"]
        expected_repos = {"repo3": "https://local-repo3.com"}
        actual_repos = {key: repo.url for key, repo in merged_poetry.config.repositories.items()}
        self.assertEqual(expected_repos, actual_repos)


if __name__ == "__main__":
    unittest.main()
