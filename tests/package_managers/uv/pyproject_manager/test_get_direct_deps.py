import unittest

from splat.model import Dependency, DependencyType
from splat.package_managers.uv.pyproject_manager import UvPyprojectManager
from tests.mocks import MockFileSystem


class TestUvGetDirectDeps(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.pyproject_manager = UvPyprojectManager(self.mock_fs)

    def test_uv_extract_all_the_deps_from_pyproject(
        self,
    ) -> None:
        mock_toml_content = """
        [project]
        name = "example"
        version = "0.1.0"
        description = ""
        authors = ["Author <author@example.com>"]
        requires-python = "~=3.8"
        dependencies = [
        "requests ~= x.y.z",
        "flask==x.y.z"
        ]

        [tool.uv]
        dev-dependencies = [
        "pytest>=x.y.z",
        ]
        """
        pyproject_path = "/path/to/pyproject.toml"
        self.mock_fs.write(pyproject_path, mock_toml_content)
        direct_deps = self.pyproject_manager.get_direct_deps(pyproject_path)
        expected_deps = [
            Dependency(
                name="requests",
                type=DependencyType.DIRECT,
                is_dev=False,
            ),
            Dependency(
                name="flask",
                type=DependencyType.DIRECT,
                is_dev=False,
            ),
            Dependency(
                name="pytest",
                type=DependencyType.DIRECT,
                is_dev=True,
            ),
        ]
        self.assertListEqual(direct_deps, expected_deps)
