import unittest
from pathlib import Path
from typing import cast

from splat.config.config_loader import load_project_config
from splat.config.model import LocalConfig, LogLevel, PMConfig
from tests.mocks import MockFileSystem, MockLogger


class TestLocalConfigModelValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_logger = MockLogger()
        self.mock_fs = MockFileSystem()
        self.dummy_path = Path("/dummy_path.yaml")

    def test_local_config_complete(self) -> None:
        complete_local_config_yaml = """
        general:
          logging:
            level: "ERROR"
          debug:
            skip_cleanup: False
        notifications:
          use_global_config: false
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
        self.mock_fs.write(str(self.dummy_path), complete_local_config_yaml)

        config = load_project_config(self.dummy_path, self.mock_logger, self.mock_fs)
        self.assertIsInstance(config, LocalConfig)
        config = cast(LocalConfig, config)
        # assert general config
        self.assertIsNotNone(config.general)
        if config.general:
            self.assertIsNotNone(config.general.logging)
            if config.general.logging:
                self.assertEqual(config.general.logging.level, LogLevel.ERROR)
            self.assertIsNotNone(config.general.debug)
            if config.general.debug:
                self.assertFalse(config.general.debug.skip_cleanup)
        # assert notifications config
        self.assertIsNotNone(config.notifications)
        if config.notifications:
            self.assertFalse(config.notifications.use_global_config)
            self.assertEqual(config.notifications.sinks[0].type, "teams")
        # assert hooks config
        self.assertIsNotNone(config.hooks)
        if config.hooks:
            self.assertTrue(config.hooks.use_global_config)  # True by default
            self.assertEqual(
                config.hooks.pre_commit["*.py"].script,
                ["black ${SPLAT_MATCHED_FILES}"],
            )
            self.assertEqual(config.hooks.pre_commit["*.py"].cwd, "${SPLAT_PROJECT_ROOT}")
            self.assertFalse(config.hooks.pre_commit["*.py"].one_command_per_file)
        # assert package managers config
        self.assertIsNotNone(config.package_managers)
        if config.package_managers:
            self.assertIsInstance(config.package_managers.pipenv, PMConfig)
            pipenv_config = cast(PMConfig, config.package_managers.pipenv)
            self.assertTrue(pipenv_config.enabled)
            self.assertIsInstance(config.package_managers.yarn, PMConfig)
            yarn_config = cast(PMConfig, config.package_managers.yarn)
            self.assertFalse(yarn_config.enabled)
            self.assertIsInstance(config.package_managers.poetry, PMConfig)
            poetry_config = cast(PMConfig, config.package_managers.pipenv)
            self.assertTrue(poetry_config.enabled)
        # assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "INFO: Loading Project specific configuration from /dummy_path.yaml",
                    "DEBUG: Project-specific configuration loaded and validated successfully.",
                ]
            )
        )

    def test_local_config_missing_values(self) -> None:
        missing_values_local_config_yaml = """
        general:
          logging:

        package_managers:
          pipenv:
            enabled: True
          yarn:
            enabled: False
        """
        self.mock_fs.write(str(self.dummy_path), missing_values_local_config_yaml)

        config = load_project_config(self.dummy_path, self.mock_logger, self.mock_fs)
        self.assertIsInstance(config, LocalConfig)
        config = cast(LocalConfig, config)
        # assert general config
        self.assertIsNotNone(config.general)
        if config.general:
            self.assertIsNone(config.general.logging)
            self.assertIsNone(config.general.debug)
        # assert notifications config
        self.assertIsNone(config.notifications)
        # assert package managers config
        self.assertIsNotNone(config.package_managers)
        if config.package_managers:
            self.assertIsInstance(config.package_managers.pipenv, PMConfig)
            pipenv_config = cast(PMConfig, config.package_managers.pipenv)
            self.assertTrue(pipenv_config.enabled)
            self.assertIsInstance(config.package_managers.yarn, PMConfig)
            yarn_config = cast(PMConfig, config.package_managers.yarn)
            self.assertFalse(yarn_config.enabled)
            self.assertIsNone(config.package_managers.poetry)
        # assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "INFO: Loading Project specific configuration from /dummy_path.yaml",
                    "DEBUG: Project-specific configuration loaded and validated successfully.",
                ]
            )
        )

    def test_local_config_empty(self) -> None:
        empty_local_config_yaml = """"""
        self.mock_fs.write(str(self.dummy_path), empty_local_config_yaml)

        config = load_project_config(self.dummy_path, self.mock_logger, self.mock_fs)
        self.assertIsNone(config)

        # Assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "INFO: Loading Project specific configuration from /dummy_path.yaml",
                    "ERROR: Project-specific configuration file /dummy_path.yaml is empty or invalid. "
                    + "Using default settings.",
                ]
            )
        )

    def test_local_config_file_does_not_exist(self) -> None:
        non_existing_file = Path("non_existing_config.yaml")
        config = load_project_config(non_existing_file, self.mock_logger, self.mock_fs)
        self.assertIsNone(config)

        # Assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                "INFO: Project specific configuration file non_existing_config.yaml not found. Using default settings."
            )
        )

    def test_invalid_local_config_logs_the_error_and_returns_none(self) -> None:
        invalid_local_config_yaml = """
        general:
          logging:
            level: "UNKNOWN_LEVEL"
        """
        self.mock_fs.write(str(self.dummy_path), invalid_local_config_yaml)

        config = load_project_config(self.dummy_path, self.mock_logger, self.mock_fs)
        self.assertIsNone(config)

        # Assert logs
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "INFO: Loading Project specific configuration from /dummy_path.yaml",
                    "ERROR: Configuration validation failed: Field 'general -> logging -> level' - "
                    "Input should be 'ERROR', 'WARNING', 'INFO' or 'DEBUG'\nWhile trying to parse:\n"
                    "{'general': {'logging': {'level': 'UNKNOWN_LEVEL'}}}",
                ]
            )
        )


if __name__ == "__main__":
    unittest.main()
