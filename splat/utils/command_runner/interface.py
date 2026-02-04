from abc import ABC, abstractmethod
from pathlib import Path
from typing import NamedTuple

from splat.interface.logger import LoggerInterface


class CommandResult(NamedTuple):
    exit_code: int
    stdout: str
    stderr: str


class CommandRunner(ABC):
    def __init__(self, logger: LoggerInterface) -> None:
        self.logger = logger

    @abstractmethod
    def run(
        self,
        cmd: str,
        args: list[str],
        cwd: Path,
        shell: bool = False,
        check: bool = True,
        stdout: int | None = None,
        stderr: int | None = None,
        allowed_return_codes: list[int] | None = None,
    ) -> CommandResult:
        pass
