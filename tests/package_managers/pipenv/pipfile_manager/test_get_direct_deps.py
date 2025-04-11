import unittest

from splat.model import Dependency, DependencyType
from splat.package_managers.pipenv.pipfile_manager import PipfileManager
from tests.mocks import MockFileSystem, MockLogger


class TestGetDirectDeps(unittest.TestCase):
    MOCK_PIPFILE_PATH = "/path/to/pipfile"

    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.manager = PipfileManager(self.mock_fs, self.mock_logger)

    def _write_mock_pipfile(self, content: str) -> None:
        """
        Helper to write mock Pipfile content to the file system.
        """
        self.mock_fs.write(self.MOCK_PIPFILE_PATH, content)

    def test_should_extract_all_dependencies_from_pipfile(self) -> None:
        mock_pipfile_content = """
        [[source]]
        url = "https://pypi.org/simple"
        verify_ssl = true
        name = "pypi"

        [packages]
        requests = "==1.1.1"
        flask = "==2.2.2"
        other = {version = "0.3.0", index = "repo"}

        [dev-packages]
        pytest = "==3.3.3"
        otherdev = {version = "5.3.0", index = "repo"}
        """
        self._write_mock_pipfile(mock_pipfile_content)

        # Expected dependencies
        expected_deps = [
            Dependency(name="requests", version="1", type=DependencyType.DIRECT, is_dev=False),
            Dependency(name="flask", version="2", type=DependencyType.DIRECT, is_dev=False),
            Dependency(name="other", version="0", type=DependencyType.DIRECT, is_dev=False),
            Dependency(name="pytest", version="3", type=DependencyType.DIRECT, is_dev=True),
            Dependency(name="otherdev", version="5", type=DependencyType.DIRECT, is_dev=True),
        ]

        direct_deps = self.manager.get_direct_deps(self.MOCK_PIPFILE_PATH)

        self.assertListEqual(direct_deps, expected_deps)


if __name__ == "__main__":
    unittest.main()
