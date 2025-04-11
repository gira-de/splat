import unittest

from splat.package_managers.poetry.pyproject_manager import PoetryPyprojectManager
from tests.mocks import MockFileSystem, MockLogger


class TestPoetryGetRequiredPythonVersion(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.pyproject_manager = PoetryPyprojectManager(self.mock_fs, self.mock_logger)

    def test_valid_python_version(self) -> None:
        mock_toml_content = """
        [tool.poetry.dependencies]
        python = "^3.8"
        """
        pyproject_path = "/path/to/pyproject.toml"
        self.mock_fs.write(pyproject_path, mock_toml_content)

        python_version = self.pyproject_manager.get_required_python_version(pyproject_path)
        self.assertEqual(python_version, "python3.8")

    def test_python_version_with_specifiers(self) -> None:
        mock_toml_content = """
        [tool.poetry.dependencies]
        python = ">=3.7"
        """
        pyproject_path = "/path/to/pyproject.toml"
        self.mock_fs.write(pyproject_path, mock_toml_content)

        python_version = self.pyproject_manager.get_required_python_version(pyproject_path)
        self.assertEqual(python_version, "python3.7")

    def test_no_python_version_specified(self) -> None:
        # Mock the content where Python version is not specified
        mock_toml_content = """
        [tool.poetry.dependencies]
        some_package = "1.0.0"
        """
        pyproject_path = "/path/to/pyproject.toml"
        self.mock_fs.write(pyproject_path, mock_toml_content)

        python_version = self.pyproject_manager.get_required_python_version(pyproject_path)
        self.assertIsNone(python_version)
        self.assertTrue(self.mock_logger.has_logged("Python version not specified"))


if __name__ == "__main__":
    unittest.main()
