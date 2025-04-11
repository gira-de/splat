import base64
import unittest
from pathlib import Path

from splat.package_managers.yarn.repo_manager import YarnRepoManager
from tests.mocks import MockEnvManager, MockFileSystem, MockLogger


class TestSetNpmrc(unittest.TestCase):
    def setUp(self) -> None:
        self.env_manager = MockEnvManager()
        self.fs = MockFileSystem()
        self.logger = MockLogger()
        self.repo_manager = YarnRepoManager(self.env_manager, self.fs, self.logger)
        self.project_path = Path("/path/project")
        self._set_credentials()

    def _set_credentials(self) -> None:
        self.env_manager.set("PASS", "pass")
        self.env_manager.set("TOKEN", "token")

    def test_npmrc_creation_with_token_scoped_repo(self) -> None:
        repo_name = "@my-org/private-repo"
        repo_url = "https://my.private.repo/simple/"
        token = self.env_manager.get("TOKEN")
        npmrc_path = self.project_path / ".npmrc"

        self.repo_manager.set_npmrc(repo_name, repo_url, self.project_path, token=token)
        content = self.fs.read(str(npmrc_path))

        expected_lines = [
            f"{repo_name}:registry={repo_url}",
            f"//my.private.repo/simple/:_authToken={token}",
            "always-auth=true",
        ]
        expected = "\n".join(expected_lines) + "\n"

        self.assertEqual(content, expected)
        self.assertTrue(self.logger.has_logged(f".npmrc file updated at {npmrc_path} with scoped configuration."))

    def test_npmrc_creation_with_token_unscoped_repo(self) -> None:
        repo_name = "private-repo"
        repo_url = "https://my.private.repo/simple/"
        token = self.env_manager.get("TOKEN")
        npmrc_path = self.project_path / ".npmrc"

        self.repo_manager.set_npmrc(repo_name, repo_url, self.project_path, token=token)
        content = self.fs.read(str(npmrc_path))

        expected_lines = [
            f"registry={repo_url}",
            f"//my.private.repo/simple/:_authToken={token}",
            "always-auth=true",
        ]
        expected = "\n".join(expected_lines) + "\n"

        self.assertEqual(content, expected)

    def test_npmrc_creation_with_basic_auth_scoped_repo(self) -> None:
        repo_name = "@my-org/private-repo"
        repo_url = "https://my.private.repo/simple/"
        username = "user"
        password = self.env_manager.get("PASS")
        npmrc_path = self.project_path / ".npmrc"

        self.repo_manager.set_npmrc(repo_name, repo_url, self.project_path, username=username, password=password)
        content = self.fs.read(str(npmrc_path))

        auth_string = f"{username}:{password}"
        encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        expected_lines = [
            f"{repo_name}:registry={repo_url}",
            f"//my.private.repo/simple/:_auth={encoded_auth}",
            "always-auth=true",
        ]
        expected = "\n".join(expected_lines) + "\n"

        self.assertEqual(content, expected)

    def test_npmrc_creation_with_basic_auth_unscoped_repo(self) -> None:
        repo_name = "private-repo"
        repo_url = "https://my.private.repo/simple/"
        username = "user"
        password = self.env_manager.get("PASS")
        npmrc_path = self.project_path / ".npmrc"

        self.repo_manager.set_npmrc(repo_name, repo_url, self.project_path, username=username, password=password)
        content = self.fs.read(str(npmrc_path))

        auth_string = f"{username}:{password}"
        encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        expected_lines = [
            f"registry={repo_url}",
            f"//my.private.repo/simple/:_auth={encoded_auth}",
            "always-auth=true",
        ]
        expected = "\n".join(expected_lines) + "\n"

        self.assertEqual(content, expected)

    def test_no_credentials_provided(self) -> None:
        repo_name = "private-repo"
        repo_url = "https://my.private.repo/simple/"
        npmrc_path = self.project_path / ".npmrc"

        self.repo_manager.set_npmrc(repo_name, repo_url, self.project_path)
        self.assertFalse(self.fs.exists(str(npmrc_path)))
        self.assertTrue(self.logger.has_logged("No credentials provided; skipping .npmrc update."))

    def test_appending_to_existing_npmrc(self) -> None:
        repo_name = "@my-org/private-repo"
        repo_url = "https://my.private.repo/simple/"
        token = self.env_manager.get("TOKEN")
        npmrc_path = self.project_path / ".npmrc"

        # Pre-create an existing .npmrc file with some content.
        self.fs.write(str(npmrc_path), "existing=content\n")

        self.repo_manager.set_npmrc(repo_name, repo_url, self.project_path, token=token)
        content = self.fs.read(str(npmrc_path))

        expected_lines = [
            "existing=content",
            f"{repo_name}:registry={repo_url}",
            f"//my.private.repo/simple/:_authToken={token}",
            "always-auth=true",
        ]
        expected = "\n".join(expected_lines) + "\n"

        self.assertEqual(content, expected)

    def test_domain_extraction_with_port(self) -> None:
        repo_name = "@my-org/private-repo"
        repo_url = "https://my.private.repo:8080/simple/"
        token = self.env_manager.get("TOKEN")
        npmrc_path = self.project_path / ".npmrc"

        self.repo_manager.set_npmrc(repo_name, repo_url, self.project_path, token=token)
        content = self.fs.read(str(npmrc_path))

        # The domain should include the port.
        expected_lines = [
            f"{repo_name}:registry={repo_url}",
            f"//my.private.repo:8080/simple/:_authToken={token}",
            "always-auth=true",
        ]
        expected = "\n".join(expected_lines) + "\n"

        self.assertEqual(content, expected)


if __name__ == "__main__":
    unittest.main()
