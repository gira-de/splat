import unittest

import toml

from splat.model import Dependency, DependencyType
from splat.package_managers.pipenv.PipenvPackageManager import PipenvPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestPipenvUpdate(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.pipenv_manager = PipenvPackageManager(
            self.mock_config, self.mock_command_runner, self.mock_fs, self.mock_logger
        )
        self.mock_pipfile_content = toml.dumps({"packages": {"package1": ">=1.0.0", "package2": ">=1.0.0"}})
        self.mock_fs.write("/path/to/project/Pipfile", self.mock_pipfile_content)

    def test_pipenv_updates_direct_dependency(self) -> None:
        vuln_report = self.audit_report

        files_to_commit = self.pipenv_manager.update(vuln_report)

        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/usr/local/bin/pipenv", args=["upgrade", "--ignore-pipfile", "package1==2.0.0"]
            )
        )
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/local/bin/pipenv", args=["update", "--dev"]))
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/local/bin/pipenv", args=["run", "pip", "freeze"]))
        self.assertEqual(
            files_to_commit,
            [
                str(vuln_report.lockfile.path),
                str(vuln_report.lockfile.path.parent / self.pipenv_manager.manifest_file_name),
            ],
        )

    def test_pipenv_update_transitive_dependency_with_parent_deps(self) -> None:
        vuln_report = self.audit_report
        vuln_report.dep.type = DependencyType.TRANSITIVE  # change type to transitive
        vuln_report.dep.parent_deps = [Dependency(name="package2", version="1", type=DependencyType.DIRECT)]

        files_to_commit = self.pipenv_manager.update(vuln_report)

        # Ensure pipenv upgrade is NOT called for transitive dependencies
        self.assertFalse(
            self.mock_command_runner.has_called(
                cmd="/usr/local/bin/pipenv", args=["upgrade", "--ignore-pipfile", "package1==2.0.0"]
            )
        )
        self.assertEqual(
            toml.dumps({"packages": {"package1": ">=1.0.0", "package2": "~=1.0"}}),
            self.mock_fs.files["/path/to/project/Pipfile"],
        )
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/local/bin/pipenv", args=["update", "--dev"]))
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/local/bin/pipenv", args=["run", "pip", "freeze"]))
        self.assertEqual(
            files_to_commit,
            [
                str(vuln_report.lockfile.path),
                str(vuln_report.lockfile.path.parent / self.pipenv_manager.manifest_file_name),
            ],
        )

    def test_pipenv_update_skips_when_fixed_version_is_none(self) -> None:
        vuln_report = self.audit_report
        vuln_report.fixed_version = None
        vuln_report.fix_skip_reason = "No fix available"

        with self.assertRaises(RuntimeError):
            self.pipenv_manager.update(vuln_report)


if __name__ == "__main__":
    unittest.main()
