from pathlib import Path
from typing import Optional

from splat.interface.logger import LoggerInterface
from splat.utils.command_runner.interface import CommandRunner
from splat.utils.fs import FileSystemInterface


class PoetryCommandRunner:
    def __init__(self, runner: CommandRunner, fs: FileSystemInterface, logger: LoggerInterface):
        self.runner = runner
        self.fs = fs
        self.logger = logger

    def env_use(self, python_version: str, cwd: Path) -> None:
        python_version_full_path = f"/usr/bin/{python_version}"
        result = self.runner.run(
            cmd="/splat/.local/bin/poetry",
            args=["env", "use", python_version_full_path],
            cwd=cwd,
        )
        self.logger.debug(result.stdout)

    def sync(self, cwd: Path) -> None:
        result = self.runner.run(
            cmd="/splat/.local/bin/poetry",
            args=["sync", "--all-groups"],
            cwd=cwd,
        )
        self.logger.debug(result.stdout)

    def export(self, cwd: Path) -> None:
        requirements_file_path = cwd / "requirements.txt"
        result = self.runner.run(
            cmd="/splat/.local/bin/poetry",
            args=["export", "--without-hashes", "--all-groups"],
            cwd=cwd,
        )
        self.fs.write(str(requirements_file_path), result.stdout)

    def run_pip_audit(self, cwd: Path) -> str:
        result = self.runner.run(
            cmd="/splat/.local/bin/poetry",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            cwd=cwd,
            allowed_return_codes=[1],
        )
        return result.stdout

    def add(self, dep_name: str, dep_version: Optional[str], cwd: Path, is_dev: bool) -> None:
        args = ["add"]
        if is_dev:
            args.extend(["--group", "dev"])
        if dep_version is None:
            args.append(dep_name)
        else:
            args.append(f"{dep_name}@^{dep_version}")
        result = self.runner.run(
            cmd="/splat/.local/bin/poetry",
            args=args,
            cwd=cwd,
        )
        self.logger.debug(result.stdout)

    def lock(self, cwd: Path) -> None:
        result = self.runner.run(
            cmd="/splat/.local/bin/poetry",
            args=["lock", "--no-update"],
            cwd=cwd,
        )
        self.logger.debug(result.stdout)
