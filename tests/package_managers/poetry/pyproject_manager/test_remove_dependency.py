import unittest

import tomlkit

from splat.package_managers.poetry.pyproject_manager import PoetryPyprojectManager
from tests.mocks import MockFileSystem, MockLogger


class TestPoetryRemoveDependency(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.manager = PoetryPyprojectManager(self.mock_fs, self.mock_logger)
        self.path = "/project/pyproject.toml"

    def test_when_regular_dependency_exists_removes_it_and_keeps_other_dependencies(self) -> None:
        content = """
        [tool.poetry]
        name = "demo"
        [tool.poetry.dependencies]
        python = ">=3.11"
        dep1 = "0.100.0"
        dep2 = "1.2.0"
        """
        self.mock_fs.write(self.path, content)
        removed = self.manager.remove_dependency(self.path, "dep2", is_dev=False)
        self.assertTrue(removed)
        updated = tomlkit.parse(self.mock_fs.read(self.path))
        deps = updated.get("tool", None).get("poetry").get("dependencies")
        self.assertNotIn("dep2", deps)
        self.assertIn("dep1", deps)

    def test_when_dev_dependency_exists_removes_it_and_keeps_other_dependencies(self) -> None:
        content = """
        [tool.poetry]
        name = "demo"
        [tool.poetry.group.dev.dependencies]
        dep1 = "^7.4"
        dep2 = "^24.0"
        """
        self.mock_fs.write(self.path, content)
        removed = self.manager.remove_dependency(self.path, "dep2", is_dev=True)
        self.assertTrue(removed)
        updated = tomlkit.parse(self.mock_fs.read(self.path))
        dev_deps = updated.get("tool", None).get("poetry").get("group").get("dev").get("dependencies")
        self.assertNotIn("dep2", dev_deps)
        self.assertIn("dep1", dev_deps)

    def test_when_dependency_missing_returns_false_and_does_not_modify_file(self) -> None:
        content = """
        [tool.poetry]
        name = "demo"
        [tool.poetry.dependencies]
        python = ">=3.11"
        """
        self.mock_fs.write(self.path, content)
        removed = self.manager.remove_dependency(self.path, "fastapi", is_dev=False)
        self.assertFalse(removed)
        self.assertEqual(self.mock_fs.read(self.path), content)
