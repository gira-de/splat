import os

from splat.utils.env_manager.interface import EnvManager


class OsEnvManager(EnvManager):
    """Default implementation using os.environ."""

    def set(self, key: str, value: str) -> None:
        os.environ[key] = value

    def get(self, key: str) -> str:
        env_var = os.environ.get(key)
        if env_var is None:
            raise EnvironmentError(f"Environment variable '{key}' must be set.")
        self.logger.debug(f"Environment variable '{key}' has been successfully loaded.")
        return env_var
