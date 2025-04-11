import base64
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from splat.config.model import RepoConfig
from splat.interface.logger import LoggerInterface
from splat.utils.env_manager.interface import EnvManager
from splat.utils.fs import FileSystemInterface
from splat.utils.logging_utils import log_authentication_type, log_invalid_credentials


class YarnRepoManager:
    def __init__(self, env_manager: EnvManager, fs: FileSystemInterface, logger: LoggerInterface):
        self.env_manager = env_manager
        self.fs = fs
        self.logger = logger

    def _generate_registry_auth_path(self, repo_url: str) -> str:
        parsed_url = urlparse(repo_url)
        registry_auth_path = parsed_url.netloc + parsed_url.path
        if not registry_auth_path.endswith("/"):
            registry_auth_path += "/"
        return registry_auth_path

    def set_npmrc(
        self,
        repo_name: str,
        repo_url: str,
        cwd: Path,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        npmrc_file = cwd / ".npmrc"
        registry_auth_path = self._generate_registry_auth_path(repo_url)
        current_content = self.fs.read(str(npmrc_file)) if self.fs.exists(str(npmrc_file)) else ""
        lines = []
        # Determine registry line based on @; scoped or unscoped
        registry_line = f"{repo_name}:registry={repo_url}" if repo_name.startswith("@") else f"registry={repo_url}"

        if token:
            auth_line = f"//{registry_auth_path}:_authToken={token}"
        elif username and password:
            auth_string = f"{username}:{password}"
            encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
            auth_line = f"//{registry_auth_path}:_auth={encoded_auth}"
        else:
            self.logger.debug("No credentials provided; skipping .npmrc update.")
            return

        lines.append(registry_line)
        lines.append(auth_line)
        lines.append("always-auth=true")
        new_content = (current_content.strip() + "\n" if current_content.strip() else "") + "\n".join(lines) + "\n"
        self.fs.write(str(npmrc_file), new_content)
        config_type = "scoped" if repo_name.startswith("@") else "unscoped"
        self.logger.debug(f".npmrc file updated at {npmrc_file} with {config_type} configuration.")

    def configure_repositories(self, expected_repos: dict[str, RepoConfig], cwd: Path) -> None:
        if not expected_repos:
            return

        for repo_name, repo_config in expected_repos.items():
            creds = repo_config.credentials
            if creds:
                if creds.username and creds.password:
                    log_authentication_type(self.logger, repo_name, "HTTP basic")
                    res_user = self.env_manager.resolve_value(creds.username)
                    res_pass = self.env_manager.resolve_value(creds.password)
                    # Update ~/.npmrc with credentials.
                    self.set_npmrc(repo_name, repo_config.url, cwd, res_user, res_pass)
                elif creds.token:
                    log_authentication_type(self.logger, repo_name, "token")
                    res_token = self.env_manager.resolve_value(creds.token)
                    self.set_npmrc(repo_name, repo_config.url, cwd, token=res_token)
                else:
                    log_invalid_credentials(self.logger, repo_name)
