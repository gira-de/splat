import unittest
from unittest.mock import MagicMock, patch

from splat.config.model import PlatformConfig
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.utils.plugin_initializer.source_control_init import (
    get_git_platform_class,
    initialize_git_platforms,
)


class TestGitPlatformInitializer(unittest.TestCase):
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
        # Test with empty config
        empty_config: list[PlatformConfig] = []
        with self.assertRaises(Exception):
            platform_interfaces = initialize_git_platforms(empty_config)
            self.assertEqual(platform_interfaces, [])

    @patch("splat.utils.plugin_initializer.source_control_init.logger")
    def test_initialize_git_platforms_initializes_a_platform_and_logs_correct_information(
        self, mock_logger: MagicMock
    ) -> None:
        valid_config = PlatformConfig(
            type="github",
            domain="mock_domain",
            access_token="mock_access",
        )  # nosec
        platform_interfaces = initialize_git_platforms([valid_config])

        # Assertions
        self.assertEqual(len(platform_interfaces), 1)
        mock_logger.debug.assert_called_once_with(
            "Source control platform 'github': '' configured successfully with no filters."
        )
        mock_logger.info.assert_called_with("Configured 1 source control platforms:'github': ''")

    @patch("splat.utils.plugin_initializer.source_control_init.get_git_platform_class")
    @patch("splat.utils.plugin_initializer.source_control_init.logger")
    def test_initialize_git_platforms_handles_exceptions(
        self, mock_logger: MagicMock, mock_get_git_platform_class: MagicMock
    ) -> None:
        # Setup to raise an exception
        mock_get_git_platform_class.side_effect = Exception("Test Exception")

        config_with_error = PlatformConfig(type="github")
        with self.assertRaises(Exception):
            initialize_git_platforms([config_with_error])

        mock_logger.error.assert_called_once_with(
            "Error configuring source control platform: 'github': '': Test Exception"
        )

    @patch("splat.utils.logging_utils.logger.error")
    def test_initialize_git_platforms_handles_validation_error(self, mock_logger_error: MagicMock) -> None:
        invalid_config = PlatformConfig(
            type="github",
            domain="invalid_domain",
        )

        with self.assertRaises(Exception):
            platform_interfaces = initialize_git_platforms([invalid_config])
            # Assertions: No platforms should be initialized, and an error should be logged
            self.assertEqual(platform_interfaces, [])

        mock_logger_error.assert_called_once_with(
            "Validation error in platform configuration for github: Field 'access_token' - Field required"
        )


if __name__ == "__main__":
    unittest.main()
