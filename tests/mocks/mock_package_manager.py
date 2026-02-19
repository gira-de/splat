from __future__ import annotations

from pathlib import Path

from splat.config.model import PMConfig
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import AuditReport, Lockfile, Project, RuntimeContext


class MockPackageManager(PackageManagerInterface):
    def __init__(self, lockfile: Lockfile | None, lockfile_name: str, config: PMConfig, ctx: RuntimeContext) -> None:
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
        return self._lockfile_name

    def run_audit_command(self, cwd: Path, re_audit: bool = False) -> str:
        return '"empty"'

    def run_real_audit_command(self, cwd: Path) -> str:
        return '"empty"'

    def find_lockfiles(self, project: Project) -> list[Lockfile]:
        if self.lockfile is not None:
            return [self.lockfile]
        return super().find_lockfiles(project)

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
