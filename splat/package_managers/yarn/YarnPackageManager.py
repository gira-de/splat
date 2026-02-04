from pathlib import Path

from splat.config.model import PMConfig
from splat.interface.logger import LoggerInterface
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import AuditReport, DependencyType, Lockfile
from splat.package_managers.yarn.audit_parser import parse_yarn_audit_output
from splat.package_managers.yarn.command_runner import YarnCommandRunner
from splat.package_managers.yarn.package_json_manager import PackageJsonManager
from splat.package_managers.yarn.repo_manager import YarnRepoManager
from splat.utils.command_runner.interface import CommandRunner
from splat.utils.fs import FileSystemInterface


class YarnPackageManager(PackageManagerInterface):
    def __init__(
        self,
        config: PMConfig,
        command_runner: CommandRunner | None = None,
        fs: FileSystemInterface | None = None,
        logger: LoggerInterface | None = None,
    ) -> None:
        super().__init__(config, command_runner, fs, logger)
        self.yarn = YarnCommandRunner(self.command_runner, self.logger)
        self.package_manager = PackageJsonManager(self.fs, self.logger)
        self.repo_manager = YarnRepoManager(self.env_manager, self.fs, self.logger)

    @property
    def name(self) -> str:
        return "yarn"

    @property
    def manifest_file_name(self) -> str:
        return "package.json"

    @property
    def lockfile_name(self) -> str:
        return "yarn.lock"

    def install(self, lockfile: Lockfile) -> None:
        self.repo_manager.configure_repositories(self.config.repositories, lockfile.path.parent)
        self.yarn.install(lockfile.path.parent)

    def run_real_audit_command(self, cwd: Path) -> str:
        return self.yarn.audit(cwd)

    def audit(self, lockfile: Lockfile, re_audit: bool = False) -> list[AuditReport]:
        audit_output = self.run_audit_command(lockfile.path.parent, re_audit)
        return parse_yarn_audit_output(audit_output, lockfile)

    def update(self, vuln_report: AuditReport) -> list[str]:
        init_log_msg = f"""{vuln_report.dep.name} from {vuln_report.dep.version} to {vuln_report.fixed_version} in {
            vuln_report.lockfile.relative_path
        }"""
        log_msg = ""
        skip_error = (
            f"Skipping update for {vuln_report.dep.name} {vuln_report.dep.version}: {vuln_report.fix_skip_reason}"
        )
        try:
            if vuln_report.fixed_version is None:
                self.logger.error(skip_error)
                raise RuntimeError(skip_error)

            files_to_commit: list[str] = [
                str(vuln_report.lockfile.path),
                str(vuln_report.lockfile.path.parent / self.manifest_file_name),
            ]

            if vuln_report.dep.type in (DependencyType.TRANSITIVE, DependencyType.BOTH):
                log_msg = f"Updating sub-dependency: {init_log_msg}"
                self.logger.info(log_msg)
                package_json_path = vuln_report.lockfile.path.parent / self.manifest_file_name
                if self.fs.exists(str(package_json_path)):
                    self.package_manager.add_resolutions_block_to_package_json(
                        str(package_json_path),
                        vuln_report.dep.name,
                        vuln_report.fixed_version,
                    )
                    self.logger.debug("Running 'yarn install' to apply resolutions")
                    self.yarn.install(vuln_report.lockfile.path.parent)
                    self.logger.info(f"Successfully updated sub-dependency: {init_log_msg}")
                else:
                    error_msg = f"{self.manifest_file_name} not found. Cannot add resolutions."
                    self.logger.error(error_msg)
                    raise RuntimeError(error_msg)

            if vuln_report.dep.type in (DependencyType.DIRECT, DependencyType.BOTH):
                log_msg = f"Updating dependency: {init_log_msg}"
                self.logger.info(log_msg)
                self.yarn.upgrade(
                    dep_name=vuln_report.dep.name,
                    dep_version=vuln_report.fixed_version,
                    cwd=vuln_report.lockfile.path.parent,
                )
                self.logger.info(f"Successfully updated dependency: {init_log_msg}")

        except RuntimeError as e:
            raise RuntimeError(f"Failed in {log_msg}: {e}")

        return files_to_commit
