from pathlib import Path
from typing import Optional

from splat.config.model import PMConfig
from splat.interface.logger import LoggerInterface
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import AuditReport, DependencyType, Lockfile
from splat.package_managers.common.pip_audit_parser import parse_pip_audit_output
from splat.package_managers.uv.command_runner import UvCommandRunner
from splat.package_managers.uv.pyproject_manager import UvPyprojectManager
from splat.package_managers.uv.repo_manager import UvRepoManager
from splat.utils.command_runner.interface import CommandRunner
from splat.utils.fs import FileSystemInterface


class UvPackageManager(PackageManagerInterface):
    def __init__(
        self,
        config: PMConfig,
        command_runner: Optional[CommandRunner] = None,
        fs: Optional[FileSystemInterface] = None,
        logger: Optional[LoggerInterface] = None,
    ) -> None:
        super().__init__(config, command_runner, fs, logger)
        self.uv = UvCommandRunner(self.command_runner, self.logger)
        self.pyproject_manager = UvPyprojectManager(self.fs)
        self.repo_manager = UvRepoManager(self.env_manager, self.fs, self.logger)

    @property
    def name(self) -> str:
        return "uv"

    @property
    def manifest_file_name(self) -> str:
        return "pyproject.toml"

    @property
    def lockfile_name(self) -> str:
        return "uv.lock"

    def install(self, lockfile: Lockfile) -> None:
        indexes = self.pyproject_manager.get_indexes(str(lockfile.path.parent / self.manifest_file_name))
        self.repo_manager.configure_repositories(self.config.repositories, indexes)
        self.uv.sync(lockfile.path.parent)
        self.uv.add(dep_name="pip-audit", dep_version=None, cwd=lockfile.path.parent, is_dev=True)

    def run_real_audit_command(self, cwd: Path) -> str:
        self.uv.export(cwd)
        return self.uv.run_pip_audit(cwd)

    def audit(self, lockfile: Lockfile, re_audit: bool = False) -> list[AuditReport]:
        audit_ouput = self.run_audit_command(lockfile.path.parent, re_audit)
        direct_deps = self.pyproject_manager.get_direct_deps(str(lockfile.path.parent / self.manifest_file_name))
        return parse_pip_audit_output(audit_ouput, direct_deps, lockfile)

    def update(self, vuln_report: AuditReport) -> list[str]:
        init_log_msg = f"""{vuln_report.dep.name} from {vuln_report.dep.version} to {
            vuln_report.fixed_version} in {vuln_report.lockfile.relative_path}"""
        try:
            if vuln_report.fixed_version is None:
                raise RuntimeError(
                    f"Skipping update for {vuln_report.dep.name} {vuln_report.dep.version}: "
                    f"{vuln_report.fix_skip_reason}"
                )

            pyproject_file_path = vuln_report.lockfile.path.parent / self.manifest_file_name
            files_to_commit: list[str] = [
                str(vuln_report.lockfile.path),
                str(pyproject_file_path),
            ]

            if vuln_report.dep.type == DependencyType.TRANSITIVE:
                self.logger.info(f"Updating sub-dependency: {init_log_msg}")
                self.uv.upgrade(
                    dep_name=vuln_report.dep.name,
                    dep_version=vuln_report.fixed_version,
                    cwd=vuln_report.lockfile.path.parent,
                    is_dev=vuln_report.dep.is_dev,
                )
                self.logger.info(f"Successfully updated sub-dependency: {init_log_msg}")
            else:
                self.logger.info(f"Updating dependency: {init_log_msg}")
                self.uv.add(
                    dep_name=vuln_report.dep.name,
                    dep_version=vuln_report.fixed_version,
                    cwd=vuln_report.lockfile.path.parent,
                    is_dev=vuln_report.dep.is_dev,
                )
                self.logger.info(f"Successfully updated dependency: {init_log_msg}")
            return files_to_commit
        except RuntimeError as e:
            raise RuntimeError(f"Failed to Update {init_log_msg}: {e}")
