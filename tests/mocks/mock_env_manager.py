from splat.utils.env_manager.interface import EnvManager


class MockEnvManager(EnvManager):
    """
    A mock implementation of EnvManager for unit testing.
    It stores environment variables in an internal dictionary.
    """

    def __init__(self) -> None:
        self._env: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self._env[key] = value

    def get(self, key: str) -> str:
        if key not in self._env:
            raise EnvironmentError(f"Environment variable '{key}' must be set.")
        return self._env[key]
