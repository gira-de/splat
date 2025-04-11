from abc import ABC, abstractmethod
from pathlib import Path
from typing import NamedTuple, Optional

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
        stdout: Optional[int] = None,
        stderr: Optional[int] = None,
        allowed_return_codes: Optional[list[int]] = None,
    ) -> CommandResult:
        pass
