from pathlib import Path

from splat.interface.logger import LoggerInterface
from splat.utils.command_runner.interface import CommandRunner


class UvCommandRunner:
    def __init__(self, runner: CommandRunner, logger: LoggerInterface):
        self.runner = runner
        self.logger = logger

    def sync(self, cwd: Path) -> None:
        result = self.runner.run(
            cmd="/usr/local/bin/uv",
            args=["sync", "--dev"],
            cwd=cwd,
        )
        self.logger.debug(f"{result.stdout}\n{result.stderr}")

    def export(self, cwd: Path) -> None:
        self.runner.run(
            cmd="/usr/local/bin/uv",
            args=["export", "--no-emit-project", "--dev", "--no-hashes", "-o", "requirements.txt"],
            cwd=cwd,
        )

    def run_pip_audit(self, cwd: Path) -> str:
        result = self.runner.run(
            cmd="/usr/local/bin/uv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            cwd=cwd,
            allowed_return_codes=[1],
        )
        return result.stdout

    def add(self, dep_name: str, dep_version: str | None, cwd: Path, is_dev: bool) -> None:
        args = ["add"]
        if is_dev:
            args.append("--dev")
        if dep_version is None:
            args.append(f"{dep_name}")
        else:
            args.append(f"{dep_name}~={dep_version}")
        result = self.runner.run(
            cmd="/usr/local/bin/uv",
            args=args,
            cwd=cwd,
        )
        self.logger.debug(f"{result.stdout}\n{result.stderr}")

    def upgrade(self, dep_name: str, dep_version: str, cwd: Path, is_dev: bool) -> None:
        result = self.runner.run(
            cmd="/usr/local/bin/uv",
            args=["lock", "--upgrade-package", f"{dep_name}~={dep_version}"],
            cwd=cwd,
        )
        self.logger.debug(f"{result.stdout}\n{result.stderr}")
