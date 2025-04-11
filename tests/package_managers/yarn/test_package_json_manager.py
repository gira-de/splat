import json
import unittest

from splat.package_managers.yarn.package_json_manager import PackageJsonManager
from tests.mocks import MockFileSystem, MockLogger


class TestYarnPackageJsonManager(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_fs = MockFileSystem()
        self.mock_logger = MockLogger()
        self.package_manager = PackageJsonManager(self.mock_fs, self.mock_logger)

    def test_add_resolutions_block_to_package_json(self) -> None:
        # Mock the content of the package.json file
        mock_package_json_content = '{"dependencies":{}, "devDependencies":{}}'
        package_json_path = "/path/to/project/package.json"
        dep_name = "sub_package"
        dep_fixed_version = "1.1.1"

        self.mock_fs.write(package_json_path, mock_package_json_content)

        self.package_manager.add_resolutions_block_to_package_json(package_json_path, dep_name, dep_fixed_version)

        actual_written_content = self.mock_fs.read(package_json_path)

        updated_package_json_content = json.loads(actual_written_content)
        expected_resolutions = {dep_name: f"^{dep_fixed_version}"}

        self.assertEqual(updated_package_json_content.get("resolutions"), expected_resolutions)


if __name__ == "__main__":
    unittest.main()
