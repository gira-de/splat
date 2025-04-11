import unittest

from splat.package_managers.uv.pyproject_manager import UvPyprojectManager
from tests.mocks import MockFileSystem


class TestUVGetIndexes(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.pyproject_manager = UvPyprojectManager(self.mock_fs)
        self.pyproject_path = "/path/to/pyproject.toml"

    def test_get_indexes_multiple_entries(self) -> None:
        # Valid TOML with multiple index entries (list)
        content = """
        [tool.uv]
        index = [
            { name = "repo1", url = "https://example.com/repo1" },
            { name = "repo2", url = "https://example.com/repo2" }
        ]
        """
        self.mock_fs.write(self.pyproject_path, content)
        expected = {"repo1": "https://example.com/repo1", "repo2": "https://example.com/repo2"}
        result = self.pyproject_manager.get_indexes(self.pyproject_path)
        self.assertEqual(result, expected)

    def test_get_indexes_no_index_key(self) -> None:
        # TOML without [tool.uv.index] returns an empty dict
        content = """
        [tool.uv]
        version = "1.0.0"
        """
        self.mock_fs.write(self.pyproject_path, content)
        expected: dict[str, str] = {}
        result = self.pyproject_manager.get_indexes(self.pyproject_path)
        self.assertEqual(result, expected)

    def test_get_indexes_incomplete_entry(self) -> None:
        # TOML with entries missing "name" or "url" - only complete entries are returned
        content = """
        [tool.uv]
        index = [
            { name = "repo1", url = "https://example.com/repo1" },
            { name = "repo2" },
            { url = "https://example.com/repo3" }
        ]
        """
        self.mock_fs.write(self.pyproject_path, content)
        expected = {"repo1": "https://example.com/repo1"}
        result = self.pyproject_manager.get_indexes(self.pyproject_path)
        self.assertEqual(result, expected)

    def test_get_indexes_fs_read_exception(self) -> None:
        # fs.read raises an exception (simulate file not found)
        with self.assertRaises(Exception) as context:
            self.pyproject_manager.get_indexes("dummy_path")
        self.assertIn("File dummy_path not found.", str(context.exception))

    def test_get_indexes_invalid_toml(self) -> None:
        # Invalid TOML content should raise an exception from toml.loads
        content = "invalid toml content"
        self.mock_fs.write(self.pyproject_path, content)
        with self.assertRaises(Exception) as context:
            self.pyproject_manager.get_indexes(self.pyproject_path)
        self.assertIn("Found invalid character in key name:", str(context.exception))


if __name__ == "__main__":
    unittest.main()
