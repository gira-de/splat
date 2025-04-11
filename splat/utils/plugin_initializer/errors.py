class PackageManagersConfigurationError(Exception):
    def __init__(self, error: Exception) -> None:
        message = f"Error configuring package managers: {error}"
        super().__init__(message)
        self.error = error
        self.message = message


class SourceControlConfigError(Exception):
    def __init__(self, platform: str, error: Exception) -> None:
        message = f"Error configuring source control platform: {platform}: {error}"
        super().__init__(message)
        self.message = message
        self.error = error
        self.platform = platform


class SourceControlsConfigurationError(Exception):
    def __init__(self, errors: list[SourceControlConfigError]) -> None:
        message = "No source control platform was configured."
        message += "\n".join(error.message for error in errors)
        super().__init__(message)
        self.errors = errors
