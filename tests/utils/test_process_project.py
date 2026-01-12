import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from splat.config.model import Config, PlatformConfig
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    MergeRequest,
    ProjectSummary,
    RemoteProject,
    Severity,
    VulnerabilityDetail,
)
from splat.package_managers.yarn.YarnPackageManager import YarnPackageManager
from splat.utils.command_runner.interface import CommandResult
from splat.utils.project_processor.single_project import process_remote_project
from tests.mocks import MockCommandRunner, MockFileSystem, MockGitClient, MockGitPlatform, MockLogger


class TestProcessProjectIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_logger = MockLogger()
        self.mock_command_runner = MockCommandRunner(self.mock_logger)
        self.mock_fs = MockFileSystem()
        self.project = RemoteProject(
            id=1,
            web_url="mock_web_url",
            clone_url="mock_clone_url",
            name_with_namespace="group/project",
            default_branch="main",
        )
        self.project.path = Path("/mock/path/project1/")
        self.lockfile = Lockfile(path=Path("/mock/path/project1/yarn.lock"), relative_path=Path("yarn.lock"))

    @patch("splat.utils.project_processor.single_project.get_logfile_url")
    @patch("splat.utils.project_processor.single_project.shutil.rmtree")
    @patch.object(PackageManagerInterface, "find_lockfiles")
    @patch("splat.utils.project_processor.single_project.load_project_config", return_value=None)
    def test_process_project_with_vulnerabilities(
        self,
        _: MagicMock,
        mock_find_lockfiles: MagicMock,
        mock_rmtree: MagicMock,
        mock_get_logfile_url: MagicMock,
    ) -> None:
        global_config = Config()
        yarn_manager = YarnPackageManager(
            global_config.package_managers.yarn, self.mock_command_runner, self.mock_fs, self.mock_logger
        )
        mock_git_platform = MockGitPlatform(config=PlatformConfig(type="mock"), projects=[self.project])

        mock_notification_sink = MagicMock()
        # Mock find_lockfiles to return one lockfile
        mock_find_lockfiles.return_value = [self.lockfile]

        git_client = MockGitClient(repo_path=self.project.path)

        # Mock audit command: One fixable vulnerability, one non-fixable
        with open("tests/utils/mock_audit_output.json") as file:
            first_audit_output = json.load(file)
        with open("tests/utils/mock_re_audit_output.json") as file:
            re_audit_output = json.load(file)

        mock_first_audit_output = "\n".join(json.dumps(row) for row in first_audit_output)
        mock_re_audit_output = "\n".join(json.dumps(row) for row in re_audit_output)

        self.mock_command_runner.set_response(
            cmd="/usr/bin/yarn",
            args=["audit", "--json"],
            response=[
                CommandResult(exit_code=0, stdout=mock_first_audit_output, stderr=""),
                CommandResult(exit_code=0, stdout=mock_re_audit_output, stderr=""),
            ],
        )

        # Mock for manager.update: First succeeds by default, second fails
        self.mock_command_runner.set_response(
            cmd="/usr/bin/yarn",
            args=["upgrade", "package2@3.0.0"],  # Attempting second update
            response=CommandResult(exit_code=1, stdout="", stderr="error"),
        )

        mock_get_logfile_url.return_value = None

        # Expected
        expected_files_to_commit = ["/mock/path/project1/yarn.lock", "/mock/path/project1/package.json"]
        expected_remaining_vulns = [
            AuditReport(
                dep=Dependency(name="package2", version="1.0.0", type=DependencyType.DIRECT, parent_deps=[]),
                severity=Severity.HIGH,
                fixed_version="3.0.0",
                vuln_details=[
                    VulnerabilityDetail(
                        id="2",
                        description="Some vulnerability description here",
                        recommendation=["Upgrade to version 3.0.0 or later"],
                        aliases=["CVE-1"],
                    )
                ],
                lockfile=self.lockfile,
            )
        ]

        expected_project_summary = ProjectSummary(
            project_name=self.project.name_with_namespace,
            time_stamp=datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%dT%H:%M:%SZ"),
            project_url=self.project.web_url,
            status_report="error",
            severity_score="high",
            mr_url="url",
            logfile_url=None,
        )

        # Call the function under test
        summary_result = process_remote_project(
            project=self.project,
            package_managers=[yarn_manager],  # Managers to test
            git_platform=mock_git_platform,  # Mock Git platform for this test
            notification_sinks=[mock_notification_sink],  # Mock notification sinks
            global_config=global_config,
            git_client=git_client,
        )

        # Assertions

        self.assertEqual(summary_result, expected_project_summary)

        branch_name = global_config.general.git.branch_name

        # Assert checks out branch
        self.assertIn(branch_name, git_client.local_branches)
        self.assertEqual(git_client.current_branch, branch_name)

        # Assert Finds lockfiles
        mock_find_lockfiles.assert_called_once_with(self.project)

        # Assert yarn install command
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["install"]))

        # Assert audit command: called 2 times, audit and re-audit
        self.assertEqual(self.mock_command_runner.call_count("/usr/bin/yarn", ["audit", "--json"]), 2)

        # assert update command is called twice, one success, one failure
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["upgrade", "package1@2.0.0"]))

        # Assert commit changes: only one commit
        self.assertEqual(len(git_client.commit_calls), 1)
        committed_files, commit_message = git_client.commit_calls[0]
        self.assertCountEqual(committed_files, expected_files_to_commit)
        self.assertIn("Security", commit_message)
        self.assertIn("package1", commit_message)

        # Assert push changes
        self.assertEqual(git_client.push_calls, [branch_name])

        self.assertEqual(len(git_client.discard_calls), 1)
        self.assertIsNone(git_client.discard_calls[0])

        # Assert sends notification
        mock_notification_sink.send_merge_request_notification.assert_called_once_with(
            merge_request=MergeRequest("Splat Dependency Updates", "url", "project_url", "project_name", "pull_mock"),
            commit_messages=[commit_message],
            remaining_vulns=expected_remaining_vulns,
        )

        # Assert cleans up the project directory via shutil.rmtree
        mock_rmtree.assert_called_once_with(self.project.path)


if __name__ == "__main__":
    unittest.main()
