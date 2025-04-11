import subprocess  # nosec
from pathlib import Path
from typing import Optional

from splat.interface.logger import LoggerInterface
from splat.utils.command_runner.interface import CommandResult, CommandRunner
from splat.utils.command_runner.safe_run import is_command_whitelisted
from splat.utils.errors import CommandExecutionError
from splat.utils.logger_config import default_logger

PIPE = subprocess.PIPE
CompletedProcess = subprocess.CompletedProcess


class SubprocessCommandRunner(CommandRunner):
    def __init__(self, logger: Optional[LoggerInterface] = None) -> None:
        self.logger = logger or default_logger
        super().__init__(self.logger)

    def run(
        self,
        cmd: str,
        args: list[str],
        cwd: Path,
        shell: bool = False,
        check: bool = True,
        stdout: Optional[int] = PIPE,
        stderr: Optional[int] = PIPE,
        allowed_return_codes: Optional[list[int]] = None,
    ) -> CommandResult:
        if not is_command_whitelisted(cmd, args):
            raise RuntimeError(f"Command '{cmd} {' '.join(args)}' is not whitelisted.")
        self.logger.debug(f"Executing: {cmd} {' '.join(args)} in {cwd}")

        try:
            cp = subprocess.run(
                [cmd, *args],
                shell=shell,
                check=check,
                cwd=cwd,
                stdout=stdout,
                stderr=stderr,
                text=True,
            )  # nosec B602
            # Only trusted commands from COMMAND_WHITELIST and args (excluding flags "--") from COMMAND_ARGS_WHITELIST
            # are allowed, hence this is a safe procedure
            return CommandResult(cp.returncode, cp.stdout, cp.stderr)
        except subprocess.CalledProcessError as e:
            # If the exit code is allowed, return the result instead of raising.
            if allowed_return_codes and e.returncode in allowed_return_codes:
                return CommandResult(e.returncode, e.stdout, e.stderr)
            stderr_output = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
            error_msg = f"Error running command: {' '.join(e.cmd)}\nError output: {stderr_output}"
            raise CommandExecutionError(error_msg) from e
