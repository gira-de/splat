import unittest
from pathlib import Path

from splat.config.config_loader import load_config
from splat.config.model import LogLevel
from tests.mocks import MockFileSystem, MockLogger


class TestConfigModelValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_logger = MockLogger()
        self.mock_fs = MockFileSystem()
        self.dummy_path = Path("/dummy_path.yaml")

    def test_global_config_complete(self) -> None:
        complete_config_yaml = """
        general:
          logging:
            level: "DEBUG"
          git:
            clone_dir: "/splat/splat_repos/"
            branch_name: "splat"
          debug:
            skip_cleanup: False
        source_control:
          platforms:
            - type: gitlab
              domain: "https://gitlab.com"
              access_token: "dummy_token"
              filters:
                exclude: []
                include: []
        notifications:
          sinks:
            - type: teams
              webhook_url: "https://dummy.webhook.url"
        hooks:
          pre_commit:
            "*.py":
              script:
                - "black ${SPLAT_MATCHED_FILES}"
              cwd: "${SPLAT_PROJECT_ROOT}"
              one_command_per_file: false
        package_managers:
          pipenv:
            enabled: true
          yarn:
            enabled: false
          poetry:
            enabled: true
        """
        self.mock_fs.write(str(self.dummy_path), complete_config_yaml)

        config = load_config(self.dummy_path, self.mock_logger, self.mock_fs)
        # assert general config
        self.assertEqual(config.general.logging.level, LogLevel.DEBUG)
        self.assertEqual(config.general.git.clone_dir, "/splat/splat_repos/")
        self.assertFalse(config.general.debug.skip_cleanup)
        # assert source control config
        self.assertEqual(len(config.source_control.platforms), 1)
        self.assertEqual(config.source_control.platforms[0].type, "gitlab")
        # assert notification config
        self.assertEqual(config.notifications.sinks[0].type, "teams")
        # assert hooks config
        self.assertIsNotNone(config.hooks)
        if config.hooks:
            self.assertEqual(
                config.hooks.pre_commit["*.py"].script,
                ["black ${SPLAT_MATCHED_FILES}"],
            )
            self.assertEqual(config.hooks.pre_commit["*.py"].cwd, "${SPLAT_PROJECT_ROOT}")
            self.assertFalse(config.hooks.pre_commit["*.py"].one_command_per_file)
        # assert package managers config
        self.assertTrue(config.package_managers.pipenv.enabled)
        self.assertFalse(config.package_managers.yarn.enabled)
        self.assertTrue(config.package_managers.poetry.enabled)
        # assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "INFO: Loading global configuration from /dummy_path.yaml",
                    "DEBUG: Global configuration loaded and validated successfully.",
                ]
            )
        )

    def test_global_config_missing_values(self) -> None:
        missing_values_config_yaml = """
        general:
          logging:
          git:
            clone_dir: "/some_repo/"

        package_managers:
          pipenv:
          yarn:
        """
        self.mock_fs.write(str(self.dummy_path), missing_values_config_yaml)

        config = load_config(self.dummy_path, self.mock_logger, self.mock_fs)
        # assert general config
        self.assertEqual(config.general.logging.level, LogLevel.INFO)  # by Default
        self.assertEqual(config.general.git.clone_dir, "/some_repo/")
        self.assertEqual(config.general.git.branch_name, "splat")  # by Default
        self.assertFalse(config.general.debug.skip_cleanup)  # by Default
        # assert source control config
        self.assertEqual(config.source_control.platforms, [])
        self.assertEqual(config.notifications.sinks, [])
        # # assert package managers config
        self.assertTrue(config.package_managers.pipenv.enabled)  # Enabled by Default
        self.assertTrue(config.package_managers.yarn.enabled)  # Enabled by Default
        self.assertTrue(config.package_managers.poetry.enabled)  # Enabled by Default
        # assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "Loading global configuration from /dummy_path.yaml",
                    "DEBUG: Global configuration loaded and validated successfully.",
                ]
            )
        )

    def test_global_config_empty(self) -> None:
        empty_config_yaml = """"""
        self.mock_fs.write(str(self.dummy_path), empty_config_yaml)

        config = load_config(self.dummy_path, self.mock_logger, self.mock_fs)
        # assert general config
        self.assertEqual(config.general.logging.level, LogLevel.INFO)  # by Default
        self.assertEqual(config.general.git.clone_dir, "/splat/splat_repos/")  # by Default
        self.assertEqual(config.general.git.branch_name, "splat")  # by Default
        self.assertFalse(config.general.debug.skip_cleanup)  # by Default
        # assert source contrlo config
        self.assertEqual(config.source_control.platforms, [])
        if config.notifications:
            self.assertEqual(config.notifications.sinks, [])
        # assert package managers config
        self.assertTrue(config.package_managers.pipenv.enabled)  # Enabled by Default
        self.assertTrue(config.package_managers.yarn.enabled)  # Enabled by Default
        self.assertTrue(config.package_managers.poetry.enabled)  # Enabled by Default
        # assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "INFO: Loading global configuration from /dummy_path.yaml",
                    "DEBUG: Global configuration loaded and validated successfully.",
                ]
            )
        )

    def test_global_config_invalid_raises_runtime_error(self) -> None:
        invalid_config_yaml = """
        general:
          logging:
            level: "UNKNOWN_LEVEL"
        """
        self.mock_fs.write(str(self.dummy_path), invalid_config_yaml)

        with self.assertRaises(RuntimeError) as context:
            load_config(self.dummy_path, self.mock_logger, self.mock_fs)

        # assert the exception message
        self.assertEqual(
            str(context.exception),
            "Configuration validation error. Please check the configuration file" " and correct the issues above.",
        )

        # assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                "ERROR: Configuration validation failed: Field 'general -> logging -> level' - "
                + "Input should be 'ERROR', 'WARNING', 'INFO' or 'DEBUG'\nWhile trying to parse:\n"
                + "{'general': {'logging': {'level': 'UNKNOWN_LEVEL'}}}"
            )
        )


if __name__ == "__main__":
    unittest.main()
