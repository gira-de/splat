from pathlib import Path

from splat.interface.logger import LoggerInterface
from splat.utils.command_runner.interface import CommandRunner
from splat.utils.fs import FileSystemInterface


class PipenvCommandRunner:
    def __init__(self, runner: CommandRunner, fs: FileSystemInterface, logger: LoggerInterface):
        self.runner = runner
        self.fs = fs
        self.logger = logger

    def install(self, cwd: Path) -> None:
        result = self.runner.run(
            cmd="/splat/.local/bin/pipenv",
            args=["install", "--dev"],
            cwd=cwd,
        )
        self.logger.debug(result.stdout)

    def install_pip_audit(self, cwd: Path) -> None:
        result = self.runner.run(
            cmd="/splat/.local/bin/pipenv",
            args=["install", "pip-audit", "--dev"],
            cwd=cwd,
        )
        self.logger.debug(result.stdout)

    def requirements(self, cwd: Path) -> None:
        """Generates requirements.txt for pipenv projects based on the package manager."""
        requirements_file_path = cwd / "requirements.txt"
        result = self.runner.run(
            cmd="/splat/.local/bin/pipenv",
            args=["requirements", "--dev"],
            cwd=cwd,
        )
        self.fs.write(str(requirements_file_path), result.stdout)

    def run_pip_freeze(self, cwd: Path) -> str:
        result = self.runner.run(
            cmd="/splat/.local/bin/pipenv",
            args=["run", "pip", "freeze"],
            cwd=cwd,
        )
        return result.stdout

    def run_pip_audit(self, cwd: Path) -> str:
        result = self.runner.run(
            cmd="/splat/.local/bin/pipenv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            cwd=cwd,
            allowed_return_codes=[1],
        )
        return result.stdout

    def upgrade(self, dep_name: str, dep_version: str, cwd: Path, is_dev: bool) -> None:
        args = ["upgrade", "--ignore-pipfile"]
        if is_dev:
            args.append("--dev")
        args.append(f"{dep_name}=={dep_version}")

        result = self.runner.run(
            cmd="/splat/.local/bin/pipenv",
            args=args,
            cwd=cwd,
        )
        self.logger.debug(result.stdout)

    def graph(self, cwd: Path) -> str:
        result = self.runner.run(
            cmd="/splat/.local/bin/pipenv",
            args=["graph", "--json"],
            cwd=cwd,
        )
        return result.stdout

    def update(self, cwd: Path) -> None:
        result = self.runner.run(
            cmd="/splat/.local/bin/pipenv",
            args=["update", "--dev"],
            cwd=cwd,
        )
        self.logger.debug(result.stdout)
