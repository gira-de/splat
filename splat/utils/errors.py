class GitOperationError(Exception):
    def __init__(self, message: str, error: Exception) -> None:
        combined_message = message + f": {error}"
        super().__init__(combined_message)
        self.message = message
        self.error = error


class CommandExecutionError(Exception):
    """Custom exception raised when a command execution fails."""

    pass


# Custom exception for skipping the current lockfile iteration
class SkipLockfileProcessingError(Exception):
    pass
