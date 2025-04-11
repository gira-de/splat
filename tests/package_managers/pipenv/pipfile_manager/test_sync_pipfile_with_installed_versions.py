import unittest

import toml

from splat.package_managers.pipenv.pipfile_manager import PipfileManager
from tests.mocks import MockFileSystem, MockLogger


class TestPipenvSyncPipfileWithInstalledVersions(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.pipfile_manager = PipfileManager(self.mock_fs, self.mock_logger)

    def _assert_pipfile_content(self, mock_pipfile_path: str, expected_content: str) -> None:
        actual_content = self.mock_fs.read(mock_pipfile_path)
        expected_toml = toml.dumps(toml.loads(expected_content)).strip()
        actual_toml = toml.dumps(toml.loads(actual_content)).strip()
        self.assertEqual(actual_toml, expected_toml)

    def test_sync_pipfile_with_installed_versions(self) -> None:
        mock_pipfile_content = """
        [packages]
        requests = "*"
        flask = "~=2.0"
        other = {version = "*", index = "repo"}

        [dev-packages]
        pytest = ">=3.0"
        """
        mock_requirements = """
        requests==1.1.1
        flask==2.2.2
        other==1.0.0
        pytest==3.3.3
        """
        expected_content = """
        [packages]
        requests = "==1.1.1"
        flask = "==2.2.2"
        other = {version = "==1.0.0", index = "repo"}

        [dev-packages]
        pytest = "==3.3.3"
        """
        mock_pipfile_path = "/path/to/Pipfile"
        self.mock_fs.write(mock_pipfile_path, mock_pipfile_content)

        self.pipfile_manager.sync_pipfile_with_installed_versions(mock_pipfile_path, mock_requirements)
        self._assert_pipfile_content(mock_pipfile_path, expected_content)

    def test_sync_pipfile_with_installed_versions_handles_missing_packages(self) -> None:
        mock_pipfile_content = """
        [packages]
        requests = ">=1.0.0"

        [dev-packages]
        pytest = ">=3.0"
        """
        mock_requirements = """
        requests==1.1.1
        flask==2.2.2
        pytest==3.3.3
        """
        expected_content = """
        [packages]
        requests = "==1.1.1"

        [dev-packages]
        pytest = "==3.3.3"
        """
        mock_pipfile_path = "/path/to/Pipfile"
        self.mock_fs.write(mock_pipfile_path, mock_pipfile_content)

        self.pipfile_manager.sync_pipfile_with_installed_versions(mock_pipfile_path, mock_requirements)
        self._assert_pipfile_content(mock_pipfile_path, expected_content)
