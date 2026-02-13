from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from splat.config.model import Config
from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    Project,
    RuntimeContext,
    Severity,
    VulnerabilityDetail,
)
from splat.utils.project_processor.audit_fixer import audit_and_fix_project
from tests.mocks import MockCommandRunner, MockEnvManager, MockFileSystem, MockGitClient, MockLogger
from tests.mocks.mock_package_manager import MockPackageManager


class AuditAndFixProjectTests(TestCase):
    def setUp(self) -> None:
        self.project = Project("namespace")
        self.lockfile = Lockfile(Path("/home/user/fake/lock.mock"), Path("fake/lock.mock"))
        self.config = Config()
        self.mock_logger = MockLogger()
        self.mock_command_runner = MockCommandRunner(self.mock_logger)
        self.mock_fs = MockFileSystem()
        self.mock_env_manager = MockEnvManager()
        self.mock_ctx = RuntimeContext(self.mock_logger, self.mock_fs, self.mock_command_runner, self.mock_env_manager)
        self.package_manager = MockPackageManager(
            lockfile=self.lockfile,
            lockfile_name="lock.mock",
            config=self.config.package_managers.pipenv,
            ctx=self.mock_ctx,
        )
        self.mock_git_client = MockGitClient(self.project.path)

    def test_logs_start_of_audit(self) -> None:
        audit_and_fix_project(
            self.project, [self.package_manager], self.config, self.mock_git_client, logger=self.mock_logger
        )

        self.assertTrue(
            self.mock_logger.has_logged(
                "INFO: Auditing dependencies in lockfile 'fake/lock.mock' for security vulnerabilities..."
            )
        )

    def test_logs_start_of_reaudit(self) -> None:
        first_audit_report = AuditReport(
            dep=Dependency(
                name="package1",
                version="1.0.0",
                type=DependencyType.DIRECT,
                parent_deps=[],
            ),
            severity=Severity.MODERATE,
            fixed_version="2.0.0",
            vuln_details=[
                VulnerabilityDetail(
                    id="1",
                    description="Some vulnerability description here",
                    recommendation=["Upgrade to version 2.0.0 or later"],
                    aliases=["CVE-1"],
                )
            ],
            lockfile=self.lockfile,
        )

        # First audit returns one vuln, second audit (re-audit) returns none
        self.package_manager.audit_results = [[first_audit_report], []]
        # Update returns some files so a commit is made and re-audit is triggered
        self.package_manager.update_results = [[str(self.lockfile.path)]]

        audit_and_fix_project(
            self.project, [self.package_manager], self.config, self.mock_git_client, logger=self.mock_logger
        )

        self.assertTrue(
            self.mock_logger.has_logged(
                "INFO: Reauditing dependencies in lockfile 'fake/lock.mock' for security vulnerabilities..."
            )
        )
