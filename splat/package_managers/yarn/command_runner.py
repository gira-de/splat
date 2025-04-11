import itertools
from pathlib import Path

from splat.interface.logger import LoggerInterface
from splat.utils.command_runner.interface import CommandRunner


class YarnCommandRunner:
    def __init__(self, runner: CommandRunner, logger: LoggerInterface):
        self.runner = runner
        self.logger = logger

    def install(self, cwd: Path) -> None:
        result = self.runner.run(
            cmd="/usr/bin/yarn",
            args=["install"],
            cwd=cwd,
        )
        self.logger.debug(result.stdout)

    def audit(self, cwd: Path) -> str:
        allowed_exit_codes = [
            sum(c) for c in itertools.chain.from_iterable(itertools.combinations([2, 4, 8, 16], r) for r in range(1, 5))
        ]
        result = self.runner.run(
            cmd="/usr/bin/yarn",
            args=["audit", "--json"],
            cwd=cwd,
            allowed_return_codes=allowed_exit_codes,
        )
        return result.stdout

    def upgrade(self, dep_name: str, dep_version: str, cwd: Path) -> None:
        result = self.runner.run(
            cmd="/usr/bin/yarn",
            args=[
                "upgrade",
                f"{dep_name}@{dep_version}",
            ],
            cwd=cwd,
        )
        self.logger.debug(result.stdout)
