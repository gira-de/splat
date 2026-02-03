from pathlib import Path

from splat.config.model import PMConfig
from splat.interface.logger import LoggerInterface
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import AuditReport, DependencyType, Lockfile
from splat.package_managers.common.pip_audit_parser import parse_pip_audit_output
from splat.package_managers.pipenv.command_runner import PipenvCommandRunner
from splat.package_managers.pipenv.pipenv_graph_parser import restructure_audit_reports
from splat.package_managers.pipenv.pipfile_manager import PipfileManager
from splat.package_managers.pipenv.repo_manager import PipenvRepoManager
from splat.utils.command_runner.interface import CommandRunner
from splat.utils.fs import FileSystemInterface


class PipenvPackageManager(PackageManagerInterface):
    def __init__(
        self,
        config: PMConfig,
        command_runner: CommandRunner | None = None,
        fs: FileSystemInterface | None = None,
        logger: LoggerInterface | None = None,
    ) -> None:
        super().__init__(config, command_runner, fs, logger)
        self.pipenv = PipenvCommandRunner(self.command_runner, self.fs, self.logger)
        self.pipfile_manager = PipfileManager(self.fs, self.logger)
        self.repo_manager = PipenvRepoManager(self.env_manager, self.fs, self.logger)

    @property
    def name(self) -> str:
        return "pipenv"

    @property
    def manifest_file_name(self) -> str:
        return "Pipfile"

    @property
    def lockfile_name(self) -> str:
        return "Pipfile.lock"

    def install(self, lockfile: Lockfile) -> None:
        pipfile_path = lockfile.path.parent / self.manifest_file_name
        sources = self.pipfile_manager.get_sources(str(pipfile_path))
        self.repo_manager.configure_repositories(self.config.repositories, sources)
        self.pipenv.install(lockfile.path.parent)
        self.pipenv.install_pip_audit(lockfile.path.parent)
        pip_freeze_output = self.pipenv.run_pip_freeze(lockfile.path.parent)
        self.pipfile_manager.sync_pipfile_with_installed_versions(str(pipfile_path), pip_freeze_output)
        self.pipenv.update(lockfile.path.parent)

    def run_real_audit_command(self, cwd: Path) -> str:
        self.pipenv.requirements(cwd)
        return self.pipenv.run_pip_audit(cwd)

    def audit(self, lockfile: Lockfile, re_audit: bool = False) -> list[AuditReport]:
        pipfile_path = lockfile.path.parent / self.manifest_file_name
        audit_output = self.run_audit_command(lockfile.path.parent, re_audit)
        direct_deps = self.pipfile_manager.get_direct_deps(str(pipfile_path))
        pipenv_graph_output = self.pipenv.graph(lockfile.path.parent)
        reports = parse_pip_audit_output(audit_output, direct_deps, lockfile, self.logger)
        return restructure_audit_reports(reports, pipenv_graph_output, direct_deps)

    def update(self, vuln_report: AuditReport) -> list[str]:
        init_log_msg = (
            f"{vuln_report.dep.name} from {vuln_report.dep.version} to "
            f"{vuln_report.fixed_version} in {vuln_report.lockfile.relative_path}"
        )
        try:
            if vuln_report.fixed_version is None:
                raise RuntimeError(
                    f"Skipping update for {vuln_report.dep.name} {vuln_report.dep.version}: "
                    f"{vuln_report.fix_skip_reason}"
                )

            pipfile_path: Path = vuln_report.lockfile.path.parent / self.manifest_file_name
            files_to_commit: list[str] = [
                str(vuln_report.lockfile.path),
                str(pipfile_path),
            ]  # always commit Pipfile and Pipfile.lock

            if vuln_report.dep.type == DependencyType.TRANSITIVE and vuln_report.dep.parent_deps:
                self.logger.warning(
                    "Updating sub-dependencies directly in Pipenv projects is not possible. "
                    "This process will attempt to resolve this by upgrading the parent dependencies "
                    "to their latest minor versions."
                )
                parents_with_version = ", ".join(
                    [f"{parent_dep.name} to ~={parent_dep.version}.0" for parent_dep in vuln_report.dep.parent_deps]
                )
                self.logger.info(
                    f"Updating sub-dependency: Updating its parents: {parents_with_version} to try to fix "
                    f"{vuln_report.dep.name} in {vuln_report.lockfile.relative_path}"
                )
                self.pipfile_manager.set_parent_deps_to_latest_minor_version(
                    str(pipfile_path), vuln_report.dep.parent_deps
                )
                self.pipenv.update(vuln_report.lockfile.path.parent)
                self.logger.info(
                    f"Successfully updated the parents: {parents_with_version}. "
                    f"Note: {vuln_report.dep.name} may or may not have been resolved. "
                )
            else:
                self.logger.info(f"Updating dependency: {init_log_msg}")
                self.pipenv.upgrade(
                    vuln_report.dep.name,
                    vuln_report.fixed_version,
                    vuln_report.lockfile.path.parent,
                    is_dev=vuln_report.dep.is_dev,
                )
                self.logger.info(f"Successfully updated dependency: {init_log_msg}")
                self.pipenv.update(vuln_report.lockfile.path.parent)

            self.logger.info(f"Freezing versions in  {pipfile_path}")
            pip_freeze_output = self.pipenv.run_pip_freeze(vuln_report.lockfile.path.parent)
            self.pipfile_manager.sync_pipfile_with_installed_versions(str(pipfile_path), pip_freeze_output)
            self.logger.info("Updating to frozen versions")
            self.pipenv.update(vuln_report.lockfile.path.parent)
            return files_to_commit

        except RuntimeError as e:
            raise RuntimeError(f"Failed to Update {init_log_msg}: {e}")
