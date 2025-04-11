import json
import unittest
from pathlib import Path

from splat.model import DependencyType
from splat.package_managers.yarn.YarnPackageManager import YarnPackageManager
from splat.utils.command_runner.interface import CommandResult
from splat.utils.errors import CommandExecutionError
from tests.package_managers.base_test import BasePackageManagerTest


class TestYarnUpdateDeps(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.manager = YarnPackageManager(self.mock_config, self.mock_command_runner, self.mock_fs, self.mock_logger)

    def test_yarn_update_direct_dependency_calls_upgrade_and_returns_files_to_commit(self) -> None:
        files_to_commit = self.manager.update(self.audit_report)

        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["upgrade", "package1@2.0.0"]))
        self.mock_logger.has_logged(
            f"[INFO] Updating dependency: {self.audit_report.dep.name} from {self.audit_report.dep.version} "
            f"to {self.audit_report.fixed_version} in {self.lockfile.relative_path}"
        )
        self.mock_logger.has_logged(
            f"[INFO] Successfully updated dependency: {self.audit_report.dep.name} from {self.audit_report.dep.version}"
            f" to {self.audit_report.fixed_version} in {self.lockfile.relative_path}"
        )
        self.assertEqual(
            files_to_commit,
            [str(self.lockfile.path), str(Path("/path/to/project/package.json"))],
        )

    def test_yarn_update_transitive_dependency_adds_resolutions_and_returns_files_to_commit(self) -> None:
        self.audit_report.dep.type = DependencyType.TRANSITIVE

        package_json_path = "/path/to/project/package.json"
        self.mock_fs.write(package_json_path, json.dumps({"dependencies": {}, "devDependencies": {}}))

        files_to_commit = self.manager.update(self.audit_report)

        # Assert that add_resolutions_block_to_package_json was called
        package_json_content = json.loads(self.mock_fs.read(package_json_path))
        self.assertIn("resolutions", package_json_content)
        self.assertEqual(
            package_json_content["resolutions"].get(self.audit_report.dep.name), f"^{self.audit_report.fixed_version}"
        )
        self.mock_logger.has_logged(("[INFO] Running 'yarn install' to apply resolutions"))
        self.mock_logger.has_logged(
            f"[INFO] Successfully updated sub-dependency: {self.audit_report.dep.name} from "
            f"{self.audit_report.dep.version} to {self.audit_report.fixed_version} in {self.lockfile.relative_path}"
        )

        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["install"]))

        self.assertEqual(
            files_to_commit,
            [str(self.lockfile.path), str(Path("/path/to/project/package.json"))],
        )

    def test_yarn_update_logs_error_and_raises_exception_on_failure(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/usr/bin/yarn",
            args=["upgrade", "package1@2.0.0"],
            response=CommandResult(exit_code=1, stdout="", stderr="Upgrade failed"),
        )
        with self.assertRaises(CommandExecutionError):
            self.manager.update(self.audit_report)

    def test_yarn_update_dep_with_both_direct_and_transitive_considers_as_both(self) -> None:
        # Setup for dependency that is both direct and transitive
        self.audit_report.dep.type = DependencyType.BOTH

        package_json_path = "/path/to/project/package.json"
        self.mock_fs.write(package_json_path, json.dumps({"dependencies": {}, "devDependencies": {}}))

        files_to_commit = self.manager.update(self.audit_report)

        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/usr/bin/yarn",
                args=["upgrade", f"{self.audit_report.dep.name}@{self.audit_report.fixed_version}"],
            )
        )

        package_json_content = json.loads(self.mock_fs.read(package_json_path))
        self.assertIn("resolutions", package_json_content)
        self.assertEqual(
            package_json_content["resolutions"].get(self.audit_report.dep.name), f"^{self.audit_report.fixed_version}"
        )

        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["install"]))

        self.assertEqual(
            files_to_commit,
            [str(self.lockfile.path), package_json_path],
        )


if __name__ == "__main__":
    unittest.main()
