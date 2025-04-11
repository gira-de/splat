import unittest

import toml

from splat.model import Dependency, DependencyType
from splat.package_managers.pipenv.pipfile_manager import PipfileManager
from tests.mocks import MockFileSystem, MockLogger


class TestPipenvSetParentDepsToLatestMinorVersion(unittest.TestCase):
    def test_set_parent_deps_to_latest_minor_version_handles_nonexistent_dependencies(
        self,
    ) -> None:
        mock_pipfile_content = """
            [packages]
            requests = "==1.1.1"

            [dev-packages]
            pytest = "==3.3.3"
            """

        mock_pipfile_path = "/path/to/Pipfile"

        # Attempt to update a non-existent dependency
        parent_deps = [Dependency(name="nonexistent-package", version="1", type=DependencyType.DIRECT)]

        mock_fs = MockFileSystem()
        mock_logger = MockLogger()
        pipfile_manager = PipfileManager(mock_fs, mock_logger)
        mock_fs.write(mock_pipfile_path, mock_pipfile_content)

        pipfile_manager.set_parent_deps_to_latest_minor_version(mock_pipfile_path, parent_deps)

        # The content should remain unchanged
        actual_pipfile_content = mock_fs.read(mock_pipfile_path)
        expected_toml = toml.dumps(toml.loads(mock_pipfile_content)).strip()
        actual_toml = toml.dumps(toml.loads(actual_pipfile_content)).strip()
        self.assertEqual(expected_toml, actual_toml)
