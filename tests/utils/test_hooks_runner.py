import subprocess  # nosec
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from splat.config.model import HooksPreCommitConfig
from splat.utils.hooks_runner import (
    _replace_placeholders,
    run_pre_commit_hooks,
    run_pre_commit_script,
)
from splat.utils.logger_config import logger


class TestHooksRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.changed_files = ["/path/to/file1.py", "/path/to/file2.js"]
        self.lockfile = MagicMock(path=Path("/path/to/lockfile"))
        self.manifestfile = Path("/path/to/manifest.json")
        self.project_root = Path("/path/to/project")
        self.expected_replacements = {
            "${SPLAT_MANIFEST_FILE}": str(self.manifestfile),
            "${SPLAT_LOCK_FILE}": str(self.lockfile.path),
            "${SPLAT_PROJECT_ROOT}": str(self.project_root),
            "${SPLAT_PACKAGE_ROOT}": str(self.lockfile.path.parent),
        }

    def test_replace_placeholders(self) -> None:
        content = "echo ${SPLAT_MATCHED_FILES} ${SPLAT_MANIFEST_FILE}"
        replacements = {
            "${SPLAT_MATCHED_FILES}": "/path/to/file1.py /path/to/file2.py",
            "${SPLAT_MANIFEST_FILE}": "/path/to/package.json",
        }
        result = _replace_placeholders(content, replacements)
        self.assertEqual(result, "echo /path/to/file1.py /path/to/file2.py /path/to/package.json")

    def test_replace_placeholders_with_missing_replacement(self) -> None:
        content = "echo ${SPLAT_MATCHED_FILES} ${SPLAT_MANIFEST_FILE}"
        replacements = {
            "${SPLAT_MATCHED_FILES}": "/path/to/file1.py /path/to/file2.py",
            # "${SPLAT_MANIFEST_FILE}" is missing
        }
        with self.assertRaises(KeyError):
            _replace_placeholders(content, replacements)

    @patch("splat.utils.hooks_runner.subprocess.run")
    def test_run_pre_commit_script_with_one_command_per_file_set_to_false(self, mock_subprocess_run: MagicMock) -> None:
        mock_subprocess_run.return_value = MagicMock(stdout=b"Script executed")
        pre_commit_hook_config = HooksPreCommitConfig(
            script=["echo ${SPLAT_MATCHED_FILES}"],
            cwd="${SPLAT_PROJECT_ROOT}",
            one_command_per_file=False,
        )
        replacements = {
            **self.expected_replacements,
            "${SPLAT_MATCHED_FILES}": "/path/to/file1.py",
        }
        with self.assertLogs(logger.logger, level="DEBUG") as log:
            run_pre_commit_script(pre_commit_hook_config, replacements)
            self.assertIn(
                "Running Pre Commit Hook Script Command: echo /path/to/file1.py in /path/to/project",
                log.output[0],
            )
            self.assertIn(
                "Successfully ran the Command: echo /path/to/file1.py in /path/to/project",
                log.output[2],
            )

        mock_subprocess_run.assert_called_once_with(
            ["echo", "/path/to/file1.py"],
            cwd=Path("/path/to/project"),
            shell=False,
            check=True,
            stdout=subprocess.PIPE,
        )

    @patch("splat.utils.hooks_runner.subprocess.run")
    def test_run_pre_commit_script_with_one_command_per_file_set_to_true(self, mock_subprocess_run: MagicMock) -> None:
        mock_subprocess_run.return_value = MagicMock(stdout=b"Script executed")
        pre_commit_hook_config = HooksPreCommitConfig(
            script=["echo ${SPLAT_MATCHED_FILES}", "ls ${SPLAT_PROJECT_ROOT}"],
            cwd="${SPLAT_PROJECT_ROOT}",
            one_command_per_file=True,
        )
        replacements = {
            **self.expected_replacements,
            "${SPLAT_MATCHED_FILES}": "/path/to/file1.py /path/to/file2.py",
        }
        with self.assertLogs(logger.logger, level="DEBUG") as log:
            run_pre_commit_script(pre_commit_hook_config, replacements)
            self.assertIn(
                "Running Pre Commit Hook Script Command for file /path/to/file1.py: \n  - echo /path/to/file1.py "
                "in /path/to/project",
                log.output[0],
            )
            self.assertIn(
                "Successfully ran the Command: echo /path/to/file1.py in /path/to/project",
                log.output[2],
            )
            self.assertIn(
                "Running Pre Commit Hook Script Command for file /path/to/file2.py: \n  - echo /path/to/file2.py "
                "in /path/to/project",
                log.output[3],
            )
            self.assertIn(
                "Successfully ran the Command: echo /path/to/file2.py in /path/to/project",
                log.output[5],
            )
            self.assertIn(
                "Running Pre Commit Hook Script Command: ls /path/to/project in /path/to/project",
                log.output[6],
            )
            self.assertIn(
                "Successfully ran the Command: ls /path/to/project in /path/to/project",
                log.output[8],
            )
        expected_calls = [
            call(
                ["echo", "/path/to/file1.py"],
                cwd=Path("/path/to/project"),
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
            ),
            call(
                ["echo", "/path/to/file2.py"],
                cwd=Path("/path/to/project"),
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
            ),
            call(
                ["ls", "/path/to/project"],
                cwd=Path("/path/to/project"),
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
            ),
        ]
        mock_subprocess_run.assert_has_calls(expected_calls)

    @patch("splat.utils.hooks_runner.run_pre_commit_script")
    def test_run_pre_commit_hooks_glob_pattern(self, mock_run_pre_commit_script: MagicMock) -> None:
        pre_commit_hooks_config = {
            "*.py": HooksPreCommitConfig(
                script=["echo ${SPLAT_MATCHED_FILES}"],
                cwd="${SPLAT_PACKAGE_ROOT}",
                one_command_per_file=False,
            )
        }

        with self.assertLogs(logger.logger) as log:
            run_pre_commit_hooks(
                changed_files=self.changed_files,
                pre_commit_hooks_config=pre_commit_hooks_config,
                lockfile=self.lockfile,
                manifestfile=self.manifestfile,
                project_root=self.project_root,
            )
            self.assertIn(
                "Running pre-commit hook for pattern '*.py' with 1 matched file(s): /path/to/file1.py",
                log.output[0],
            )

        expected_replacements = {
            **self.expected_replacements,
            "${SPLAT_MATCHED_FILES}": "/path/to/file1.py",
        }

        mock_run_pre_commit_script.assert_called_once_with(pre_commit_hooks_config["*.py"], expected_replacements)

    @patch("splat.utils.hooks_runner.run_pre_commit_script")
    def test_run_pre_commit_hooks_regex_pattern(self, mock_run_pre_commit_script: MagicMock) -> None:
        pre_commit_hooks_config = {
            "/.*\\.py$/": HooksPreCommitConfig(
                script=["echo ${SPLAT_MATCHED_FILES}"],
                cwd="${SPLAT_PROJECT_ROOT}",
                one_command_per_file=False,
            )
        }

        with self.assertLogs(logger.logger) as log:
            run_pre_commit_hooks(
                changed_files=self.changed_files,
                pre_commit_hooks_config=pre_commit_hooks_config,
                lockfile=self.lockfile,
                manifestfile=self.manifestfile,
                project_root=self.project_root,
            )
            self.assertIn(
                "Running pre-commit hook for pattern '/.*\\.py$/' with 1 matched file(s): /path/to/file1.py",
                log.output[0],
            )

        expected_replacements = {
            **self.expected_replacements,
            "${SPLAT_MATCHED_FILES}": "/path/to/file1.py",
        }

        mock_run_pre_commit_script.assert_called_once_with(pre_commit_hooks_config["/.*\\.py$/"], expected_replacements)

    @patch("splat.utils.hooks_runner.run_pre_commit_script")
    def test_run_pre_commit_hooks_when_no_changed_files_matched_config_pattern(
        self, mock_run_pre_commit_script: MagicMock
    ) -> None:
        pre_commit_hooks_config = {
            "*.md": HooksPreCommitConfig(
                script=["echo ${SPLAT_MATCHED_FILES}"],
                cwd="${SPLAT_PACKAGE_ROOT}",
                one_command_per_file=False,
            )
        }
        changed_files = ["/path/to/file1.py", "/path/to/file2.js"]  # No .md files
        lockfile = MagicMock(path=Path("/path/to/lockfile"))
        manifestfile = Path("/path/to/manifest.json")
        project_root = Path("/path/to/project")

        with self.assertLogs(logger.logger) as log:
            run_pre_commit_hooks(
                changed_files=changed_files,
                pre_commit_hooks_config=pre_commit_hooks_config,
                lockfile=lockfile,
                manifestfile=manifestfile,
                project_root=project_root,
            )
            self.assertIn(
                "No matching files found for pre-commit hook pattern '*.md'. Skipping...",
                log.output[0],
            )
        # Ensuring run_pre_commit_script was not called when no matching files
        mock_run_pre_commit_script.assert_not_called()

    @patch(
        "splat.utils.hooks_runner.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "cmd"),
    )
    def test_run_pre_commit_script_error_handling_stops_the_script(self, mock_subprocess_run: MagicMock) -> None:
        pre_commit_hook_config = HooksPreCommitConfig(
            script=["echo ${SPLAT_MATCHED_FILES}", "another_command"],
            cwd="${SPLAT_PROJECT_ROOT}",
            one_command_per_file=False,
        )
        replacements = {
            "${SPLAT_MATCHED_FILES}": "/path/to/file1.py",
            "${SPLAT_PROJECT_ROOT}": "/path/to/project",
        }
        with self.assertLogs(logger.logger, level="ERROR") as log:
            run_pre_commit_script(pre_commit_hook_config, replacements)
            self.assertIn(
                "Pre-commit hook script '['echo ${SPLAT_MATCHED_FILES}', 'another_command']' failed with error",
                log.output[0],
            )

        # Ensure subprocess.run was only called once, since the first command fails and stops the script
        mock_subprocess_run.assert_called_once_with(
            ["echo", "/path/to/file1.py"],
            cwd=Path("/path/to/project"),
            shell=False,
            check=True,
            stdout=subprocess.PIPE,
        )
