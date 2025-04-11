from splat.config.model import RepoConfig, RepoCredentials
from splat.package_managers.common.base_repo_manager import BasePipRepoManager


class PoetryRepoManager(BasePipRepoManager):
    def _configure_authentication(self, repo_name: str, repo_config: RepoConfig, creds: RepoCredentials) -> None:
        repo_env_key = repo_name.upper()
        if creds.username and creds.password:
            self.logger.debug(f"Setting HTTP basic authentication for repository '{repo_name}'.")
            res_user = self.env_manager.resolve_value(creds.username)
            res_pass = self.env_manager.resolve_value(creds.password)
            self.env_manager.set(f"POETRY_HTTP_BASIC_{repo_env_key}_USERNAME", res_user)
            self.env_manager.set(f"POETRY_HTTP_BASIC_{repo_env_key}_PASSWORD", res_pass)
            self.pip_auth.set_netrc(repo_config.url, username=res_user, password=res_pass)
        elif creds.token:
            self.logger.debug(f"Setting token authentication for repository '{repo_name}'.")
            res_token = self.env_manager.resolve_value(creds.token)
            self.env_manager.set(f"POETRY_PYPI_TOKEN_{repo_env_key}", res_token)
            self.pip_auth.set_netrc(repo_config.url, token=res_token)
        else:
            self.logger.debug(f"No valid credentials provided for repository '{repo_name}', skipping authentication.")
