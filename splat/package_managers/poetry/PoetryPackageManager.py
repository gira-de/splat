from __future__ import annotations

from pathlib import Path
from typing import Optional

from splat.config.model import PMConfig
from splat.interface.logger import LoggerInterface
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import AuditReport, DependencyType, Lockfile
from splat.package_managers.common.pip_audit_parser import parse_pip_audit_output
from splat.package_managers.poetry.command_runner import PoetryCommandRunner
from splat.package_managers.poetry.pyproject_manager import PoetryPyprojectManager
from splat.package_managers.poetry.repo_manager import PoetryRepoManager
from splat.utils.command_runner.interface import CommandRunner
from splat.utils.env_manager.interface import EnvManager
from splat.utils.fs import FileSystemInterface


class PoetryPackageManager(PackageManagerInterface):
    def __init__(
        self,
        config: PMConfig,
        command_runner: Optional[CommandRunner] = None,
        fs: Optional[FileSystemInterface] = None,
        logger: Optional[LoggerInterface] = None,
        env_manager: Optional[EnvManager] = None,
    ) -> None:
        self.config = config
        super().__init__(config, command_runner, fs, logger, env_manager)
        self.poetry = PoetryCommandRunner(self.command_runner, self.fs, self.logger)
        self.repo_manager = PoetryRepoManager(self.env_manager, self.fs, self.logger)
        self.pyproject_manager = PoetryPyprojectManager(self.fs, self.logger)

    @property
    def name(self) -> str:
        return "poetry"

    @property
    def manifest_file_name(self) -> str:
        return "pyproject.toml"

    @property
    def lockfile_name(self) -> str:
        return "poetry.lock"

    def set_poetry_python_env(self, lockfile: Lockfile) -> None:
        pyproject_file_path = str(lockfile.path.parent / self.manifest_file_name)
        python_version = self.pyproject_manager.get_required_python_version(pyproject_file_path)
        if python_version is not None:
            self.poetry.env_use(python_version, lockfile.path.parent)
            # else splat automatically selects python version

    def install(self, lockfile: Lockfile) -> None:
        self.set_poetry_python_env(lockfile)
        pyproject_file_path = str(lockfile.path.parent / self.manifest_file_name)
        sources = self.pyproject_manager.get_sources(pyproject_file_path)
        self.repo_manager.configure_repositories(self.config.repositories, sources)
        self.poetry.sync(lockfile.path.parent)
        self.poetry.add(dep_name="pip-audit", dep_version=None, cwd=lockfile.path.parent, is_dev=True)

    def run_real_audit_command(self, cwd: Path) -> str:
        self.poetry.export(cwd)
        return self.poetry.run_pip_audit(cwd)

    def audit(self, lockfile: Lockfile, re_audit: bool = False) -> list[AuditReport]:
        audit_ouput = self.run_audit_command(lockfile.path.parent, re_audit)
        pyproject_file_path = str(lockfile.path.parent / self.manifest_file_name)
        direct_deps = self.pyproject_manager.get_direct_deps(pyproject_file_path)
        return parse_pip_audit_output(audit_ouput, direct_deps, lockfile, self.logger)

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
            files_to_commit: list[str] = [str(vuln_report.lockfile.path)]

            if vuln_report.dep.type == DependencyType.TRANSITIVE:
                self.logger.info(f"Updating sub-dependency: {init_log_msg}")
                self.poetry.add(
                    dep_name=vuln_report.dep.name,
                    dep_version=vuln_report.fixed_version,
                    cwd=vuln_report.lockfile.path.parent,
                    is_dev=vuln_report.dep.is_dev,
                )
                self.pyproject_manager.remove_dependency(
                    pyproject_path=str(pyproject_file_path),
                    dependency_name=vuln_report.dep.name,
                    is_dev=vuln_report.dep.is_dev,
                )
                self.poetry.lock(vuln_report.lockfile.path.parent)
                self.logger.info(f"Successfully updated sub-dependency: {init_log_msg}")
            else:
                self.logger.info(f"Updating dependency: {init_log_msg}")
                self.poetry.add(
                    dep_name=vuln_report.dep.name,
                    dep_version=vuln_report.fixed_version,
                    cwd=vuln_report.lockfile.path.parent,
                    is_dev=vuln_report.dep.is_dev,
                )
                files_to_commit.append(str(pyproject_file_path))
                self.logger.info(f"Successfully updated dependency: {init_log_msg}")
            return files_to_commit
        except RuntimeError as e:
            raise RuntimeError(f"Failed to Update {init_log_msg}: {e}")
