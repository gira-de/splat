from splat.config.model import RepoConfig, RepoCredentials
from splat.interface.logger import LoggerInterface
from splat.package_managers.common.pip_repo_auth import PipRepoAuth, normalize_url
from splat.utils.env_manager.interface import EnvManager
from splat.utils.fs import FileSystemInterface


class BasePipRepoManager:
    def __init__(self, env_manager: EnvManager, fs: FileSystemInterface, logger: LoggerInterface):
        self.env_manager = env_manager
        self.logger = logger
        self.pip_auth = PipRepoAuth(fs, logger)

    def configure_repositories(self, expected_repos: dict[str, RepoConfig], manifest_sources: dict[str, str]) -> None:
        """
        For each repository defined in the configuration (expected_repos),
        check if a matching repository exists in the manifest (parsed from pyproject.toml).
        The check verifies that both the repository name and the normalized URLs match.
        If a match is found and credentials are provided, configure authentication accordingly.
        """
        for repo_name, repo_config in expected_repos.items():
            expected_url = normalize_url(repo_config.url)
            if not self._repository_exists(repo_name, expected_url, manifest_sources):
                self.logger.warning(
                    f"Repository '{repo_name}' mismatch or not found: expected URL '{repo_config.url}', "
                    "but no matching repository was found. Skipping authentication."
                )
                continue

            self.pip_auth.set_pip_config(repo_config.url)
            creds = repo_config.credentials
            if creds:
                self._configure_authentication(repo_name, repo_config, creds)
            else:
                self.logger.debug(f"No credentials provided for repository '{repo_name}', skipping authentication.")

    def _repository_exists(self, repo_name: str, expected_url: str, manifest_sources: dict[str, str]) -> bool:
        # Check by matching repo name and normalized URL.
        if repo_name in manifest_sources:
            return normalize_url(manifest_sources[repo_name]) == expected_url
        return False

    def _configure_authentication(self, repo_name: str, repo_config: RepoConfig, creds: RepoCredentials) -> None:
        if creds.username and creds.password:
            self.logger.debug(f"Setting HTTP basic authentication for repository '{repo_name}'.")
            res_user = self.env_manager.resolve_value(creds.username)
            res_pass = self.env_manager.resolve_value(creds.password)
            self.pip_auth.set_netrc(repo_config.url, username=res_user, password=res_pass)
        elif creds.token:
            self.logger.debug(f"Setting token authentication for repository '{repo_name}'.")
            res_token = self.env_manager.resolve_value(creds.token)
            self.pip_auth.set_netrc(repo_config.url, token=res_token)
        else:
            self.logger.debug(f"No valid credentials provided for repository '{repo_name}', skipping authentication.")
