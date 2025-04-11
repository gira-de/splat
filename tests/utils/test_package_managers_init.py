import unittest

from splat.config.model import PackageManagersConfig, PMConfig
from splat.package_managers.yarn.YarnPackageManager import YarnPackageManager
from splat.utils.plugin_initializer.package_managers_init import (
    get_pm_class,
    initialize_package_managers,
)
from tests.mocks import MockLogger


class TestPackageManagerInitializer(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_logger = MockLogger()

    def test_get_pm_class_valid_type(self) -> None:
        pm_name = "yarn"
        expected_class = YarnPackageManager

        pm_class = get_pm_class(pm_name)
        # Assertions
        self.assertEqual(pm_class, expected_class)

    def test_get_pm_class_invalid_type_raises_error(self) -> None:
        pm_name = "invalid_pm"
        with self.assertRaises(ImportError):
            get_pm_class(pm_name)

    def test_initialize_package_managers_with_empty_config_enables_all_managers(self) -> None:
        # Pass empty config to initialize_package_managers
        pm_interfaces = initialize_package_managers(PackageManagersConfig(), self.mock_logger)

        # Assert that all package managers are initialized by defaullt
        self.assertEqual(len(pm_interfaces), 4)
        self.assertTrue(
            self.mock_logger.has_logged(
                "INFO: Configured package managers: 4 enabled, 0 disabled "
                "(pipenv: Enabled, yarn: Enabled, poetry: Enabled, uv: Enabled)"
            )
        )

    def test_initialize_package_managers_with_disabled_config(self) -> None:
        disabled_config = PackageManagersConfig(yarn=PMConfig(enabled=False))
        pm_interfaces = initialize_package_managers(disabled_config, self.mock_logger)

        # Since yarn is disabled, it should not be initialized
        self.assertEqual(len(pm_interfaces), 3)
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "DEBUG: Package manager 'pipenv' configured successfully: enabled",
                    "DEBUG: Package manager 'yarn' configured successfully: disabled",
                    "DEBUG: Package manager 'poetry' configured successfully: enabled",
                    "DEBUG: Package manager 'uv' configured successfully: enabled",
                    "INFO: Configured package managers: 3 enabled, 1 disabled "
                    + "(pipenv: Enabled, yarn: Disabled, poetry: Enabled, uv: Enabled)",
                ]
            )
        )

    def test_initialize_package_managers_logs_correct_information(self) -> None:
        valid_config = PackageManagersConfig(pipenv=PMConfig(enabled=True))
        pm_interfaces = initialize_package_managers(valid_config, self.mock_logger)

        # Assertions
        self.assertEqual(len(pm_interfaces), 4)
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "DEBUG: Package manager 'pipenv' configured successfully: enabled",
                    "DEBUG: Package manager 'yarn' configured successfully: enabled",
                    "DEBUG: Package manager 'poetry' configured successfully: enabled",
                    "DEBUG: Package manager 'uv' configured successfully: enabled",
                    "INFO: Configured package managers: 4 enabled, 0 disabled "
                    "(pipenv: Enabled, yarn: Enabled, poetry: Enabled, uv: Enabled)",
                ]
            )
        )


if __name__ == "__main__":
    unittest.main()
