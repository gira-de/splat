import unittest
from typing import Any

import toml

from splat.package_managers.pipenv.pipfile_manager import PipfileManager
from tests.mocks import MockFileSystem, MockLogger


class TestPipenvGetSources(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.pipfile_manager = PipfileManager(self.mock_fs, self.mock_logger)
        self.pipfile_path = "/path/to/Pipfile"
        self.pypi_url = "https://pypi.org/simple"

    def _write_pipfile(self, content: dict[str, Any]) -> None:
        """
        Helper method to write TOML content to the mock Pipfile.
        """
        pipfile_content = toml.dumps(content)
        self.mock_fs.write(self.pipfile_path, pipfile_content)

    def test_should_return_single_source(self) -> None:
        self._write_pipfile({"source": {"name": "PyPI", "url": self.pypi_url}})
        sources = self.pipfile_manager.get_sources(self.pipfile_path)
        expected = {"PyPI": self.pypi_url}
        self.assertEqual(sources, expected)

    def test_should_return_multiple_sources(self) -> None:
        self._write_pipfile(
            {
                "source": [
                    {"name": "PyPI", "url": self.pypi_url},
                    {"name": "PrivateRepo", "url": "https://nexus.example.com/repo/simple"},
                ]
            }
        )
        sources = self.pipfile_manager.get_sources(self.pipfile_path)
        expected = {"PyPI": self.pypi_url, "PrivateRepo": "https://nexus.example.com/repo/simple"}
        self.assertEqual(sources, expected)

    def test_should_return_empty_dict_when_no_sources(self) -> None:
        self._write_pipfile({"packages": {"requests": "*"}})
        sources = self.pipfile_manager.get_sources(self.pipfile_path)
        expected: dict[str, str] = {}
        self.assertEqual(sources, expected)

    def test_should_ignore_incomplete_source_entries(self) -> None:
        self._write_pipfile(
            {
                "source": [
                    {"name": "PyPI", "url": self.pypi_url},
                    {"name": "IncompleteRepo"},  # Missing URL
                    {"url": "https://nexus.example.com/repo/simple"},  # Missing name
                ]
            }
        )
        sources = self.pipfile_manager.get_sources(self.pipfile_path)
        expected = {"PyPI": self.pypi_url}
        self.assertEqual(sources, expected)

    def test_should_raise_exception_on_invalid_toml(self) -> None:
        invalid_content = "invalid_toml_content"
        self.mock_fs.write(self.pipfile_path, invalid_content)
        with self.assertRaises(Exception) as context:
            self.pipfile_manager.get_sources(self.pipfile_path)
        self.assertIn("Failed to load", str(context.exception))

    def test_should_return_empty_dict_on_empty_pipfile(self) -> None:
        self.mock_fs.write(self.pipfile_path, "")
        sources = self.pipfile_manager.get_sources(self.pipfile_path)
        expected: dict[str, str] = {}
        self.assertEqual(sources, expected)


if __name__ == "__main__":
    unittest.main()
