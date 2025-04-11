import unittest

from splat.config.config_merger import _merge_general_configs
from splat.config.model import (
    DebugConfig,
    GeneralConfig,
    GitConfig,
    LocalGeneralConfig,
    LoggingConfig,
    LogLevel,
)
from tests.mocks import MockLogger


class TestConfigMerger(unittest.TestCase):
    GLOBAL_CLONE_DIR = "/global/clone/dir"
    LOCAL_BRANCH_NAME = "local-branch"
    GLOBAL_BRANCH_NAME = "global-branch"

    def setUp(self) -> None:
        self.mock_logger = MockLogger()
        self.global_general_config = GeneralConfig(
            logging=LoggingConfig(level=LogLevel("DEBUG")),
            git=GitConfig(clone_dir=self.GLOBAL_CLONE_DIR, branch_name=self.GLOBAL_BRANCH_NAME),
            debug=DebugConfig(skip_cleanup=True),
        )

        self.local_general_config = LocalGeneralConfig(
            logging=LoggingConfig(level=LogLevel("ERROR")),
            debug=DebugConfig(skip_cleanup=False),
        )

    def test_merge_general_configs_complete_local_override(self) -> None:
        merged_config = _merge_general_configs(self.global_general_config, self.local_general_config, self.mock_logger)
        self.assertEqual(merged_config.logging.level, "ERROR")
        self.assertEqual(merged_config.git.branch_name, self.GLOBAL_BRANCH_NAME)
        self.assertEqual(merged_config.git.clone_dir, self.GLOBAL_CLONE_DIR)
        self.assertFalse(merged_config.debug.skip_cleanup)

    def test_merge_general_configs_partial_local_override(self) -> None:
        partial_local_config = LocalGeneralConfig(
            logging=LoggingConfig(level=LogLevel.ERROR),
        )
        merged_config = _merge_general_configs(self.global_general_config, partial_local_config, self.mock_logger)
        self.assertEqual(merged_config.git.branch_name, self.GLOBAL_BRANCH_NAME)
        self.assertEqual(merged_config.logging.level, "ERROR")
        self.assertTrue(merged_config.debug.skip_cleanup)  # From global

    def test_merge_general_configs_no_local_config(self) -> None:
        merged_config = _merge_general_configs(self.global_general_config, LocalGeneralConfig(), self.mock_logger)
        self.assertEqual(merged_config.logging.level, "DEBUG")
        self.assertEqual(merged_config.git.branch_name, self.GLOBAL_BRANCH_NAME)
        self.assertEqual(merged_config.git.clone_dir, self.GLOBAL_CLONE_DIR)
        self.assertTrue(merged_config.debug.skip_cleanup)

    def test_merge_general_configs_unset_fields_in_local_config(self) -> None:
        unset_fields_local_config = LocalGeneralConfig()
        merged_config = _merge_general_configs(self.global_general_config, unset_fields_local_config, self.mock_logger)
        self.assertEqual(merged_config.git.branch_name, self.GLOBAL_BRANCH_NAME)
        self.assertEqual(merged_config.git.clone_dir, self.GLOBAL_CLONE_DIR)
        self.assertEqual(merged_config.logging.level, "DEBUG")  # From global
        self.assertTrue(merged_config.debug.skip_cleanup)  # From global


if __name__ == "__main__":
    unittest.main()
