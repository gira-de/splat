import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from splat.config.model import PMConfig
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, Lockfile, Project
from splat.utils.command_runner.interface import CommandRunner
from splat.utils.command_runner.real_runner import SubprocessCommandRunner
from splat.utils.env_manager.interface import EnvManager
from splat.utils.env_manager.os import OsEnvManager
from splat.utils.fs import FileSystemInterface, RealFileSystem
from splat.utils.git_operations import is_git_ignored
from splat.utils.logger_config import default_logger
from splat.utils.logging_utils import log_found_lockfiles


class PackageManagerInterface(ABC):
    def __init__(
        self,
        config: PMConfig,
        command_runner: Optional[CommandRunner] = None,
        fs: Optional[FileSystemInterface] = None,
        logger: Optional[LoggerInterface] = None,
        env_manager: Optional[EnvManager] = None,
    ) -> None:
        self.config = config
        self.logger = logger or default_logger
        self.command_runner = command_runner or SubprocessCommandRunner(self.logger)
        self.fs = fs or RealFileSystem()
        self.env_manager = env_manager or OsEnvManager(self.logger)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def manifest_file_name(self) -> str:
        pass

    @property
    @abstractmethod
    def lockfile_name(self) -> str:
        pass

    @abstractmethod
    def install(self, lockfile: Lockfile) -> None:
        """Handles installing dependencies and audit tools before auditing."""
        pass

    def run_audit_command(self, cwd: Path, re_audit: bool = False) -> str:
        use_mock = os.getenv("MOCK_AUDIT", "false").lower() == "true"
        if use_mock:
            mock_file = "re_audit_output.json" if re_audit else "audit_output.json"
            mock_file_path = cwd / mock_file
            try:
                # Read the mock audit output as a plain string to preserve its original formatting
                with open(mock_file_path, "r") as file:
                    return file.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"Mock audit file '{mock_file}' not found at '{mock_file_path}'.")
        # Call the abstract audit command method, which each subclass must implement
        return self.run_real_audit_command(cwd)

    @abstractmethod
    def run_real_audit_command(self, cwd: Path) -> str:
        """This method should be implemented by subclasses to provide the actual audit command."""
        pass

    def find_lockfiles(self, project: Project) -> list[Lockfile]:
        found_lockfiles = [
            Lockfile(
                path=lockfile,
                relative_path=Path("/") / lockfile.relative_to(project.path),
            )
            for lockfile in project.path.rglob(self.lockfile_name)
            if is_git_ignored(str(lockfile), project.path) is False
        ]
        log_found_lockfiles(self.name, project.name_with_namespace, found_lockfiles)

        return found_lockfiles

    @abstractmethod
    def audit(self, lockfile: Lockfile, re_audit: bool = False) -> list[AuditReport]:
        """
        Audits passed lockfile using the appropriate package manager's audit command.
        Returns a list of dependencies that have vulnerabilities.
        """

    @abstractmethod
    def update(self, vuln_report: AuditReport) -> list[str]:
        pass
