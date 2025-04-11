import unittest

from splat.model import Dependency, DependencyType
from splat.package_managers.poetry.pyproject_manager import PoetryPyprojectManager
from tests.mocks import MockFileSystem, MockLogger


class TestPoetryGetDirectDeps(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.pyproject_manager = PoetryPyprojectManager(self.mock_fs, self.mock_logger)

    def test_poetry_extract_all_the_deps_from_pyproject(
        self,
    ) -> None:
        mock_toml_content = """
        [tool.poetry]
        name = "example"
        version = "0.1.0"
        description = ""
        authors = ["Author <author@example.com>"]

        [tool.poetry.dependencies]
        python = "^3.8"
        requests = "*"
        flask = "*"
        other = {version = "*", source = "repo"}

        [tool.poetry.group.dev.dependencies]
        pytest = "*"
        otherdev = {version = "*", source = "repo"}
        """

        pyproject_path = "/path/to/pyproject.toml"
        self.mock_fs.write(pyproject_path, mock_toml_content)
        direct_deps = self.pyproject_manager.get_direct_deps(pyproject_path)
        expected_deps = [
            Dependency(name="requests", type=DependencyType.DIRECT, version="*", is_dev=False),
            Dependency(name="flask", type=DependencyType.DIRECT, version="*", is_dev=False),
            Dependency(name="other", type=DependencyType.DIRECT, version="*", is_dev=False),
            Dependency(name="pytest", type=DependencyType.DIRECT, version="*", is_dev=True),
            Dependency(name="otherdev", type=DependencyType.DIRECT, version="*", is_dev=True),
        ]
        self.assertListEqual(direct_deps, expected_deps)
