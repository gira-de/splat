from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from splat.config.model import Config, PMConfig
from splat.interface.PackageManagerInterface import PackageManagerInterface
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


class PackageManagerMock(PackageManagerInterface):
    def __init__(self, lockfile: Lockfile, lockfile_name: str, config: PMConfig, ctx: RuntimeContext) -> None:
        super().__init__(config, ctx)
        self.lockfile = lockfile
        self._lockfile_name = lockfile_name
        self.audit_results: list[list[AuditReport]] = []
        self.update_results: list[list[str]] = []

    @property
    def name(self) -> str:
        return "mock"

    @property
    def manifest_file_name(self) -> str:
        return "manifest.mock"

    @property
    def lockfile_name(self) -> str:
        return "lock.mock"

    def run_audit_command(self, cwd: Path, re_audit: bool = False) -> str:
        return '"empty"'

    def run_real_audit_command(self, cwd: Path) -> str:
        return '"empty"'

    def find_lockfiles(self, project: Project) -> list[Lockfile]:
        return [self.lockfile]

    def install(self, lockfile: Lockfile) -> None:
        pass

    def audit(self, lockfile: Lockfile, re_audit: bool = False) -> list[AuditReport]:
        if self.audit_results:
            return self.audit_results.pop(0)
        return []

    def update(self, vuln_report: AuditReport) -> list[str]:
        if self.update_results:
            return self.update_results.pop(0)
        return []


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
        self.package_manager = PackageManagerMock(
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
                "[INFO] Auditing dependencies in lockfile 'fake/lock.mock' for security vulnerabilities..."
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
                "[INFO] Reauditing dependencies in lockfile 'fake/lock.mock' for security vulnerabilities..."
            )
        )
