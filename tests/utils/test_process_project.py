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
from tests.mocks import MockCommandRunner, MockFileSystem, MockGitPlatform, MockLogger


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

    @patch("splat.utils.project_processor.project_operations.checkout_branch")
    @patch("splat.utils.project_processor.single_project.load_project_config", return_value=None)
    @patch.object(PackageManagerInterface, "find_lockfiles")
    @patch("splat.utils.project_processor.audit_fixer.Repo")
    @patch("splat.utils.project_processor.audit_fixer.commit_changes")
    @patch("splat.utils.project_processor.project_operations.push_changes")
    @patch("splat.utils.project_processor.audit_fixer.discard_files_changes")
    @patch("splat.utils.project_processor.single_project.clean_up_project_dir")
    @patch("splat.utils.project_processor.single_project.get_logfile_url")
    def test_process_project_with_vulnerabilities(
        self,
        mock_get_logfile_url: MagicMock,
        mock_clean_up_project_dir: MagicMock,
        mock_discard_changes: MagicMock,
        mock_push_changes: MagicMock,
        mock_commit_changes: MagicMock,
        mock_repo: MagicMock,
        mock_find_lockfiles: MagicMock,
        _: MagicMock,
        mock_checkout_branch: MagicMock,
    ) -> None:
        global_config = Config()
        yarn_manager = YarnPackageManager(
            global_config.package_managers.yarn, self.mock_command_runner, self.mock_fs, self.mock_logger
        )
        mock_git_platform = MockGitPlatform(config=PlatformConfig(type="mock"), projects=[self.project])

        mock_notification_sink = MagicMock()
        # Mock find_lockfiles to return one lockfile
        mock_find_lockfiles.return_value = [self.lockfile]

        mock_git_repo = MagicMock()
        mock_repo.return_value = mock_git_repo

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
        mock_commit_changes.return_value = (
            "fix: Security [moderate 🟠]: Update package1 from 1.0.0 to 2.0.0 in yarn.lock\n\n"
            "This update addresses the following vulnerabilities:\n\n- Some vulnerability description here\n"
            "  - Aliases: CVE-2\n  - Recommendation: Upgrade to version 2.0.0 or later\n\n"
        )

        # Expected
        expected_audit_report = AuditReport(
            dep=Dependency(name="package1", version="1.0.0", type=DependencyType.DIRECT, parent_deps=[]),
            severity=Severity.MODERATE,
            fixed_version="2.0.0",
            vuln_details=[
                VulnerabilityDetail(
                    id="1",
                    description="Some vulnerability description here",
                    recommendation=["Upgrade to version 2.0.0 or later"],
                    aliases=["CVE-2"],
                )
            ],
            lockfile=self.lockfile,
        )
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
        )

        # Assertions

        self.assertEqual(summary_result, expected_project_summary)

        # Assert checks out branch
        mock_checkout_branch.assert_called_once_with(
            repo_path=self.project.path, branch_name=global_config.general.git.branch_name, is_local_project=False
        )

        # Assert Finds lockfiles
        mock_find_lockfiles.assert_called_once_with(self.project)

        # Assert yarn install command
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["install"]))

        # Assert audit command: called 2 times, audit and a re audit
        self.assertEqual(self.mock_command_runner.call_count("/usr/bin/yarn", ["audit", "--json"]), 2)

        # assert update command is called twice, one success, one failure
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["upgrade", "package1@2.0.0"]))

        # Assert commit changes: only one commit
        mock_commit_changes.assert_called_once_with(mock_git_repo, expected_files_to_commit, expected_audit_report)
        mock_discard_changes.assert_called_once_with(repo_path=self.project.path)

        # Assert push changes
        mock_push_changes.assert_called_once_with(
            repo_path=self.project.path, branch_name=global_config.general.git.branch_name
        )

        # Assert sends notification
        mock_notification_sink.send_merge_request_notification.assert_called_once_with(
            merge_request=MergeRequest("Splat Dependency Updates", "url", "project_url", "project_name", "pull_mock"),
            commit_messages=[mock_commit_changes.return_value],
            remaining_vulns=expected_remaining_vulns,
        )

        # Assert cleans up the project
        mock_clean_up_project_dir.assert_called_once_with(self.project.path)


if __name__ == "__main__":
    unittest.main()
