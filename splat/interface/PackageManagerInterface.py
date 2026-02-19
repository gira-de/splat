from abc import ABC, abstractmethod
from pathlib import Path

from splat.config.model import PMConfig
from splat.model import AuditReport, Lockfile, Project, RuntimeContext
from splat.utils.logging_utils import log_found_lockfiles


class PackageManagerInterface(ABC):
    def __init__(self, config: PMConfig, ctx: RuntimeContext) -> None:
        self.config = config
        self.ctx = ctx
        self.logger = ctx.logger
        self.command_runner = ctx.command_runner
        self.fs = ctx.fs
        self.env_manager = ctx.env_manager

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
        try:
            raw = self.env_manager.get("MOCK_AUDIT").lower()
        except EnvironmentError:
            raw = "false"
        use_mock = raw.strip().lower() in {"true", "1", "yes"}
        if use_mock:
            mock_file = "re_audit_output.json" if re_audit else "audit_output.json"
            mock_file_path = cwd / mock_file
            try:
                # Read the mock audit output as a plain string to preserve its original formatting
                return self.fs.read(str(mock_file_path))
            except FileNotFoundError:
                raise FileNotFoundError(f"Mock audit file '{mock_file}' not found at '{mock_file_path}'.")
        # Call the abstract audit command method, which each subclass must implement
        return self.run_real_audit_command(cwd)

    @abstractmethod
    def run_real_audit_command(self, cwd: Path) -> str:
        """This method should be implemented by subclasses to provide the actual audit command."""
        pass

    def find_lockfiles(self, project: Project) -> list[Lockfile]:
        lockfile_paths = self.fs.glob(str(project.path), f"**/{self.lockfile_name}")
        found_lockfiles = [
            Lockfile(
                path=Path(lockfile_path),
                relative_path=Path("/") / Path(lockfile_path).relative_to(project.path),
            )
            for lockfile_path in lockfile_paths
        ]
        log_found_lockfiles(self.name, project.name_with_namespace, found_lockfiles, self.logger)

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
