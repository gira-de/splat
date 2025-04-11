import unittest

from splat.package_managers.poetry.pyproject_manager import PoetryPyprojectManager
from tests.mocks import MockFileSystem, MockLogger


class TestPoetryGetSources(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.pyproject_manager = PoetryPyprojectManager(self.mock_fs, self.mock_logger)
        self.pyproject_path = "/path/to/pyproject.toml"

    def write_to_pyproject(self, content: str) -> None:
        """Helper method to write content to pyproject.toml."""
        self.mock_fs.write(self.pyproject_path, content)

    def test_multiple_source_entries(self) -> None:
        content = """
        [tool.poetry]
        source = [
            { name = "repo1", url = "https://example.com/repo1" },
            { name = "repo2", url = "https://example.com/repo2" }
        ]
        """
        self.write_to_pyproject(content)
        expected = {"repo1": "https://example.com/repo1", "repo2": "https://example.com/repo2"}
        result = self.pyproject_manager.get_sources(self.pyproject_path)
        self.assertEqual(result, expected)

    def test_no_source_key(self) -> None:
        content = """
        [tool.poetry]
        version = "1.0.0"
        """
        self.write_to_pyproject(content)
        result = self.pyproject_manager.get_sources(self.pyproject_path)
        self.assertEqual(result, {})

    def test_incomplete_source_entries(self) -> None:
        content = """
        [tool.poetry]
        source = [
            { name = "repo1", url = "https://example.com/repo1" },
            { name = "repo2" },
            { url = "https://example.com/repo3" }
        ]
        """
        self.write_to_pyproject(content)
        expected = {"repo1": "https://example.com/repo1"}
        result = self.pyproject_manager.get_sources(self.pyproject_path)
        self.assertEqual(result, expected)

    def test_fs_read_exception(self) -> None:
        with self.assertRaises(Exception) as context:
            self.pyproject_manager.get_sources("dummy_path")
        self.assertIn("File dummy_path not found", str(context.exception))

    def test_invalid_toml(self) -> None:
        content = "invalid toml content"
        self.write_to_pyproject(content)
        with self.assertRaises(Exception) as context:
            self.pyproject_manager.get_sources(self.pyproject_path)
        self.assertIn("Found invalid character in key name", str(context.exception))
