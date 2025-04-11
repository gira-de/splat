import unittest
from pathlib import Path

from splat.package_managers.common.pip_repo_auth import PipRepoAuth
from tests.mocks import MockFileSystem, MockLogger


class TestSetPipConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.fs = MockFileSystem()
        self.logger = MockLogger()
        self.updater = PipRepoAuth(self.fs, self.logger)
        self.pip_config_path = str(self.fs.home() / ".config" / "pip" / "pip.conf")

    def assert_pip_config_contains(self, expected_content: dict[str, dict[str, str]]) -> None:
        content = self.fs.files[self.pip_config_path]
        for section, values in expected_content.items():
            self.assertIn(f"[{section}]", content)
            for key, value in values.items():
                self.assertIn(f"{key} = {value}", content)

    def test_creates_pip_config_file_when_missing(self) -> None:
        repo_url = "http://example.com/simple"
        self.assertFalse(self.fs.exists(self.pip_config_path))

        self.updater.set_pip_config(repo_url)

        parent_dir = str(Path(self.pip_config_path).parent)
        self.assertIn(parent_dir, self.fs.directories)
        self.assertIn(self.pip_config_path, self.fs.files)
        self.assert_pip_config_contains({"global": {"extra-index-url": repo_url}})
        self.assertTrue(self.logger.has_logged(f"set extra-index-url to '{repo_url}'"))
        self.assertTrue(self.fs.exists(self.pip_config_path))

    def test_adds_global_section_when_missing(self) -> None:
        initial_content = "[dummy]\nkey = value\n"
        self.fs.write(self.pip_config_path, initial_content)
        repo_url = "http://example.com/simple"

        self.updater.set_pip_config(repo_url)

        self.assert_pip_config_contains({"global": {"extra-index-url": repo_url}, "dummy": {"key": "value"}})
        self.assertTrue(self.logger.has_logged(f"set extra-index-url to '{repo_url}'"))

    def test_updates_existing_global_section(self) -> None:
        initial_content = "[global]\nextra-index-url = http://old-url.com\n"
        self.fs.write(self.pip_config_path, initial_content)
        repo_url = "http://example.com/simple"

        self.updater.set_pip_config(repo_url)

        content = self.fs.files[self.pip_config_path]
        self.assertIn(f"extra-index-url = {repo_url}", content)
        self.assertEqual(content.count("[global]"), 1)
        self.assertTrue(self.logger.has_logged(f"set extra-index-url to '{repo_url}'"))


if __name__ == "__main__":
    unittest.main()
