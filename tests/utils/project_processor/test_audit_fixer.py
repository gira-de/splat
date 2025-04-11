from __future__ import annotations

import os
from pathlib import Path
from unittest import TestCase, skip
from unittest.mock import MagicMock

from splat.config.model import Config
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import AuditReport, Lockfile, Project
from splat.utils.project_processor.audit_fixer import audit_and_fix_project


class PackageManagerMock(PackageManagerInterface):
    def __init__(self, lockfile: Lockfile) -> None:
        self.lockfile = lockfile
        self.audit_results = []

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
        return []

    def update(self, vuln_report: AuditReport) -> list[str]:
        return []

    audit_results: list[list[AuditReport]]


class AuditAndFixProjectTests(TestCase):
    def test_logs_start_of_audit(self) -> None:
        project = Project("namespace")
        lockfile = Lockfile(Path(f"{os.getcwd()}/fake/lock.mock"), Path("fake/lock.mock"))
        package_manager = PackageManagerMock(lockfile)
        config = Config()
        mock_logger = MagicMock()
        audit_and_fix_project(project, [package_manager], config, None, mock_logger)
        mock_logger.info.assert_called_with(
            "Auditing dependencies in lockfile 'fake/lock.mock' for security vulnerabilities..."
        )

    @skip("""Test is currently not easy to implement, because audit_and_fix_project() also does actual
        git commands if auditing yields results.""")
    def test_logs_start_of_reaudit(self) -> None:
        pass
