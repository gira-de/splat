from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple, Union

from splat.interface.logger import LoggerInterface
from splat.utils.command_runner.interface import CommandResult, CommandRunner
from splat.utils.errors import CommandExecutionError
from tests.mocks.mock_logger import MockLogger


class CommandCall(NamedTuple):
    """Structured representation of a recorded command execution."""

    cmd: str
    args: Tuple[str, ...]
    cwd: Path
    shell: bool
    check: bool


class MockCommandRunner(CommandRunner):
    def __init__(self, logger: LoggerInterface = MockLogger()) -> None:
        super().__init__(logger)
        self.calls: List[CommandCall] = []  # Track all calls for verification
        # Store responses as queues to allow multiple responses per command
        self.responses: Dict[Tuple[str, Tuple[str, ...]], deque[CommandResult]] = defaultdict(deque)

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
        """Mocked execution of a command."""
        call = CommandCall(cmd=cmd, args=tuple(args), cwd=cwd, shell=False, check=check)
        # Record call details
        self.calls.append(call)
        key = (cmd, tuple(args))

        if key in self.responses and self.responses[key]:
            result = self.responses[key].popleft()  # Return the next response in sequence
        else:
            result = CommandResult(exit_code=0, stdout="Mocked output", stderr="")  # Default response

        if (
            check is True
            and result.exit_code != 0
            and (allowed_return_codes is None or result.exit_code not in allowed_return_codes)
        ):
            raise CommandExecutionError(
                f"Command failed: {cmd} {args} (Exit Code: {result.exit_code})\n{result.stderr}"
            )

        return result

    def set_response(self, cmd: str, args: List[str], response: Union[CommandResult, List[CommandResult]]) -> None:
        """Store single or multiple responses for a command."""
        key = (cmd, tuple(args))
        if isinstance(response, list):
            self.responses[key].extend(response)  # Add multiple responses
        else:
            self.responses[key].append(response)  # Add a single response

    def has_called(self, cmd: str, args: List[str] | None = None) -> bool:
        """Check if a command was executed at least once."""
        return any(call.cmd == cmd and (args is None or call.args == tuple(args)) for call in self.calls)

    def call_count(self, cmd: str, args: List[str] | None = None) -> int:
        """Count occurrences of a command execution."""
        return sum(1 for call in self.calls if call.cmd == cmd and (args is None or call.args == tuple(args)))
