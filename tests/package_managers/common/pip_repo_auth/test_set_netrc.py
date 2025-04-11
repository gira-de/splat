import unittest

from splat.package_managers.common.pip_repo_auth import PipRepoAuth
from tests.mocks import MockFileSystem, MockLogger


class TestSetNetrc(unittest.TestCase):
    def setUp(self) -> None:
        self.fs = MockFileSystem()
        self.logger = MockLogger()
        self.updater = PipRepoAuth(self.fs, self.logger)
        self.pip_config_path = str(self.fs.home() / ".config" / "pip" / "pip.conf")

    def test_netrc_creation_with_token(self) -> None:
        repo_url = "http://example.com"
        tk = "my_tk"
        netrc_file = str(self.fs.home() / ".netrc")
        self.updater.set_netrc(repo_url, token=tk)
        content = self.fs.read(netrc_file)
        expected = "machine example.com\n    login __token__\n    password my_tk"
        self.assertEqual(content, expected)
        self.assertTrue(self.logger.has_logged("Updated ~/.netrc with credentials for machine 'example.com'"))

    def test_netrc_creation_with_username_password(self) -> None:
        repo_url = "http://example.com"
        username = "user"
        ps = "pass"
        netrc_file = str(self.fs.home() / ".netrc")
        self.updater.set_netrc(repo_url, username=username, password=ps)
        content = self.fs.read(netrc_file)
        self.assertEqual(content, f"machine example.com\n    login {username}\n    password {ps}")
        self.assertTrue(self.logger.has_logged("Updated ~/.netrc with credentials for machine 'example.com'"))

    def test_netrc_update_existing_file(self) -> None:
        repo_url = "http://example.com"
        tk = "my_tk"
        netrc_file = str(self.fs.home() / ".netrc")
        # Prepopulate with an unrelated entry.
        initial_content = "machine other.com\n    login other\n    password otherpass\n"
        self.fs.write(netrc_file, initial_content)
        self.updater.set_netrc(repo_url, token=tk)
        content = self.fs.read(netrc_file)
        expected = (
            "machine other.com\n    login other\n    password otherpass\n"
            "machine example.com\n    login __token__\n    password my_tk"
        )
        self.assertEqual(content, expected)

    def test_netrc_insufficient_credentials(self) -> None:
        repo_url = "http://example.com"
        # No credentials provided.
        with self.assertRaises(ValueError):
            self.updater.set_netrc(repo_url)
        # Only username provided.
        with self.assertRaises(ValueError):
            self.updater.set_netrc(repo_url, username="user")
        # Only password provided.
        with self.assertRaises(ValueError):
            self.updater.set_netrc(repo_url, password="pass")  # nosec

    def test_netrc_precedence_token_over_username_password(self) -> None:
        repo_url = "http://example.com"
        tk = "my_tk"
        username = "user"
        ps = "pass"
        netrc_file = str(self.fs.home() / ".netrc")
        self.updater.set_netrc(repo_url, username=username, password=ps, token=tk)
        content = self.fs.read(netrc_file)
        # Token credentials should be used.
        self.assertEqual(content, "machine example.com\n    login __token__\n    password my_tk")
        # Username/password should not appear.
        self.assertNotIn(f"login {username}", content)
        self.assertNotIn(f"password {ps}", content)

    def test_set_netrc_no_duplicate(self) -> None:
        netrc_path = self.fs.home() / ".netrc"
        # Start with an empty .netrc file
        self.fs.write(str(netrc_path), "")

        repo_url = "https://example.com"
        user = "user1"
        ps = "pass1"

        # Call set_netrc twice
        self.updater.set_netrc(repo_url, username=user, password=ps)
        self.updater.set_netrc(repo_url, username=user, password=ps)

        content = self.fs.read(str(netrc_path))
        self.assertEqual(content, "machine example.com\n    login user1\n    password pass1")


if __name__ == "__main__":
    unittest.main()
