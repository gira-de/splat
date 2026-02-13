import unittest
from unittest.mock import MagicMock, patch

from splat.config.model import PlatformConfig
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.utils.plugin_initializer.source_control_init import (
    get_git_platform_class,
    initialize_git_platforms,
)
from tests.mocks import MockEnvManager, MockLogger


class TestGitPlatformInitializer(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = MockLogger()
        self.env_manager = MockEnvManager()

    @patch("splat.utils.plugin_initializer.source_control_init.get_class")
    def test_get_git_platform_class_valid_type(self, mock_get_class: MagicMock) -> None:
        # Setup mock class
        mock_class = MagicMock(spec=GitPlatformInterface)
        mock_get_class.return_value = mock_class

        platform_name = "github"
        platform_class = get_git_platform_class(platform_name)

        # Assertions
        mock_get_class.assert_called_once_with("splat.source_control.github.GithubPlatform", "GithubPlatform")
        self.assertEqual(platform_class, mock_class)

    @patch("splat.utils.plugin_initializer.source_control_init.get_class")
    def test_get_git_platform_class_invalid_type_raises_error(self, mock_get_class: MagicMock) -> None:
        # Simulate an error for an invalid class
        mock_get_class.side_effect = ImportError("Invalid platform type")

        platform_name = "invalid_platform"

        with self.assertRaises(ImportError):
            get_git_platform_class(platform_name)

        mock_get_class.assert_called_once_with(
            "splat.source_control.invalid_platform.Invalid_platformPlatform",
            "Invalid_platformPlatform",
        )

    def test_initialize_git_platforms_with_empty_configs(self) -> None:
        with self.assertRaises(Exception):
            initialize_git_platforms([], self.logger, self.env_manager)

    @patch("splat.utils.plugin_initializer.source_control_init.get_git_platform_class")
    def test_initialize_git_platforms_initializes_a_platform_and_logs_correct_information(
        self, mock_get_git_platform_class: MagicMock
    ) -> None:
        mock_platform_class = MagicMock(spec=GitPlatformInterface)
        mock_platform_instance = MagicMock(spec=GitPlatformInterface)
        mock_get_git_platform_class.return_value = mock_platform_class
        mock_platform_class.from_platform_config.return_value = mock_platform_instance

        valid_config = PlatformConfig(type="github")
        platform_interfaces = initialize_git_platforms([valid_config], self.logger, self.env_manager)

        self.assertEqual(len(platform_interfaces), 1)
        mock_platform_class.from_platform_config.assert_called_once_with(
            valid_config, logger=self.logger, env_manager=self.env_manager
        )
        self.assertTrue(
            self.logger.has_logged(
                [
                    "DEBUG: Source control platform 'github': '' configured successfully with no filters.",
                    "INFO: Configured 1 source control platforms:'github': ''",
                ]
            )
        )

    @patch("splat.utils.plugin_initializer.source_control_init.get_git_platform_class")
    def test_initialize_git_platforms_handles_exceptions(self, mock_get_git_platform_class: MagicMock) -> None:
        mock_get_git_platform_class.side_effect = Exception("Test Exception")

        with self.assertRaises(Exception):
            initialize_git_platforms([PlatformConfig(type="github")], self.logger, self.env_manager)

        self.assertTrue(
            self.logger.has_logged("Error configuring source control platform: 'github': '': Test Exception")
        )


if __name__ == "__main__":
    unittest.main()
