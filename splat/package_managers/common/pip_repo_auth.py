import io
from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse

from splat.interface.logger import LoggerInterface
from splat.utils.fs import FileSystemInterface


def normalize_url(url: str) -> str:
    """
    Normalize a URL by stripping any trailing slashes from its path.
    """
    parsed = urlparse(url)
    normalized_path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, normalized_path, "", "", ""))


def _update_netrc_content(existing_lines: list[str], repo_url: str, credential_lines: list[str]) -> str:
    """
    Given the existing lines of a netrc file, a repository URL,
    and the new credential lines, return the updated netrc content.
    """
    parsed = urlparse(repo_url)
    machine_line = f"machine {parsed.netloc}"
    # Skip update if machine already exists.
    if any(line.startswith(machine_line) for line in existing_lines):
        return "\n".join(existing_lines)
    new_lines = existing_lines.copy()
    new_lines.append(machine_line)
    new_lines.extend(credential_lines)
    return "\n".join(new_lines)


class PipRepoAuth:
    def __init__(self, fs: FileSystemInterface, logger: LoggerInterface) -> None:
        self.fs = fs
        self.logger = logger

    def set_pip_config(self, repo_url: str) -> None:
        """
        Update pip configuration to set the extra-index-url for the given repository.
        """
        pip_config_file = self.fs.home() / ".config" / "pip" / "pip.conf"
        config = ConfigParser()
        if self.fs.exists(str(pip_config_file)):
            existing = self.fs.read(str(pip_config_file))
            config.read_string(existing)
        if not config.has_section("global"):
            config.add_section("global")
        normalized = normalize_url(repo_url)
        config.set("global", "extra-index-url", normalized)
        self.fs.mkdir(str(pip_config_file.parent), parents=True, exist_ok=True)
        with io.StringIO() as buffer:
            config.write(buffer)
            self.fs.write(str(pip_config_file), buffer.getvalue())
        self.logger.debug(f"Updated pip config at {pip_config_file}: set extra-index-url to '{normalized}'.")

    def set_netrc(
        self, repo_url: str, username: str | None = None, password: str | None = None, token: str | None = None
    ) -> None:
        """
        Update or create the ~/.netrc file with credentials for the specified machine or repository URL.
        """
        netrc_file = self.fs.home() / ".netrc"
        parsed = urlparse(repo_url)
        if not parsed.netloc:
            raise ValueError(f"Invalid repository URL: {repo_url}")

        if self.fs.exists(str(netrc_file)):
            existing = self.fs.read(str(netrc_file)).splitlines()
        else:
            existing = []

        def _build_credentials(token: str | None, username: str | None, password: str | None) -> list[str]:
            if token:
                return ["    login __token__", f"    password {token}"]
            if username and password:
                return [f"    login {username}", f"    password {password}"]
            raise ValueError("Must provide either a token or both username and password.")

        credential_lines = _build_credentials(token, username, password)

        updated_content = _update_netrc_content(existing, repo_url, credential_lines)
        if updated_content != "\n".join(existing):  # Only write if there are changes
            self.fs.write(str(netrc_file), updated_content)
            self.logger.debug(f"Updated ~/.netrc with credentials for machine '{parsed.netloc}'.")
        else:
            self.logger.debug(f"No changes made to ~/.netrc for machine '{parsed.netloc}'.")
