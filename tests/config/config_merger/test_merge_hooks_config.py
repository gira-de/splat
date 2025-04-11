import unittest

from splat.config.config_merger import _merge_hooks_config
from splat.config.model import (
    HooksConfig,
    HooksPreCommitConfig,
    LocalHooksConfig,
)
from tests.mocks import MockLogger


class TestConfigMerger(unittest.TestCase):
    GLOBAL_CLONE_DIR = "/global/clone/dir"
    LOCAL_BRANCH_NAME = "local-branch"
    GLOBAL_BRANCH_NAME = "global-branch"

    def setUp(self) -> None:
        self.mock_logger = MockLogger()
        self.global_hooks_config = HooksConfig(
            pre_commit={
                "*.py": HooksPreCommitConfig(
                    script=["black ${SPLAT_MATCHED_FILES}"],
                    cwd="${SPLAT_PACKAGE_ROOT}",
                ),
                "tests/*.py": HooksPreCommitConfig(
                    script=["pytest ${SPLAT_MATCHED_FILES}"],
                    cwd="${SPLAT_PROJECT_ROOT}/tests",
                ),
            }
        )

        self.local_hooks_config = LocalHooksConfig(
            use_global_config=True,
            pre_commit={
                "*.js": HooksPreCommitConfig(
                    script=["eslint ${SPLAT_MATCHED_FILES}"],
                    cwd="${SPLAT_PACKAGE_ROOT}",
                ),
            },
        )

    def test_merge_hooks_config_with_global_usage(self) -> None:
        merged_hooks = _merge_hooks_config(self.global_hooks_config, self.local_hooks_config, self.mock_logger)
        self.assertIsNotNone(merged_hooks)
        if merged_hooks is not None:
            self.assertIn("*.py", merged_hooks.pre_commit)
            self.assertIn("*.js", merged_hooks.pre_commit)
            self.assertIn("tests/*.py", merged_hooks.pre_commit)
            self.assertEqual(merged_hooks.pre_commit["*.py"].script, ["black ${SPLAT_MATCHED_FILES}"])
            self.assertEqual(
                merged_hooks.pre_commit["*.js"].script,
                ["eslint ${SPLAT_MATCHED_FILES}"],
            )
            self.assertEqual(
                merged_hooks.pre_commit["tests/*.py"].script,
                ["pytest ${SPLAT_MATCHED_FILES}"],
            )
        self.assertTrue(
            self.mock_logger.has_logged('Configured 3 Pre Commit Hooks, with patterns: "*.py, tests/*.py, *.js"')
        )

    def test_merge_hooks_config_without_global_usage(self) -> None:
        local_hooks_config_no_global = self.local_hooks_config.model_copy(update={"use_global_config": False})
        merged_hooks = _merge_hooks_config(self.global_hooks_config, local_hooks_config_no_global, self.mock_logger)
        self.assertIsNotNone(merged_hooks)
        if merged_hooks is not None:
            self.assertNotIn("*.py", merged_hooks.pre_commit)
            self.assertNotIn("tests/*.py", merged_hooks.pre_commit)
            self.assertIn("*.js", merged_hooks.pre_commit)
        self.assertTrue(self.mock_logger.has_logged('Configured 1 Pre Commit Hooks, with patterns: "*.js"'))

    def test_merge_hooks_config_no_local_config(self) -> None:
        local_hooks_config_empty = LocalHooksConfig(use_global_config=True)
        merged_hooks = _merge_hooks_config(self.global_hooks_config, local_hooks_config_empty, self.mock_logger)
        self.assertEqual(merged_hooks, self.global_hooks_config)
        self.assertTrue(self.mock_logger.has_logged('Configured 2 Pre Commit Hooks, with patterns: "*.py, tests/*.py"'))

    def test_merge_hooks_config_local_pre_commit_script_overrides_global_if_the_pattern_exists_in_both(self) -> None:
        local_hooks_override = LocalHooksConfig(
            use_global_config=True,
            pre_commit={
                "*.py": HooksPreCommitConfig(
                    script=["mypy ${SPLAT_MATCHED_FILES}"],
                    cwd="${SPLAT_PACKAGE_ROOT}",
                ),
            },
        )
        merged_hooks = _merge_hooks_config(self.global_hooks_config, local_hooks_override, self.mock_logger)
        self.assertIsNotNone(merged_hooks)
        if merged_hooks is not None:
            self.assertIn("*.py", merged_hooks.pre_commit)
            self.assertEqual(merged_hooks.pre_commit["*.py"].script, ["mypy ${SPLAT_MATCHED_FILES}"])
            self.assertNotEqual(merged_hooks.pre_commit["*.py"].script, ["black ${SPLAT_MATCHED_FILES}"])
        self.assertTrue(self.mock_logger.has_logged('Configured 2 Pre Commit Hooks, with patterns: "*.py, tests/*.py"'))


if __name__ == "__main__":
    unittest.main()
