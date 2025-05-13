import unittest

from splat.model import DependencyType
from splat.package_managers.poetry.PoetryPackageManager import PoetryPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestPoetryUpdate(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.poetry_manager = PoetryPackageManager(
            self.mock_config, self.mock_command_runner, self.mock_fs, self.mock_logger
        )

    def test_update_direct_dependency(self) -> None:
        vuln_report = self.audit_report

        files_to_commit = self.poetry_manager.update(vuln_report)

        self.assertTrue(
            self.mock_command_runner.has_called(cmd="/usr/local/bin/poetry", args=["add", "package1@^2.0.0"])
        )
        self.assertFalse(self.mock_command_runner.has_called(cmd="/usr/local/bin/poetry", args=["lock", "--no-update"]))
        self.assertEqual(
            files_to_commit,
            [
                str(vuln_report.lockfile.path),
                str(vuln_report.lockfile.path.parent / self.poetry_manager.manifest_file_name),
            ],
        )

    def test_update_transitive_dependency(self) -> None:
        vuln_report = self.audit_report
        vuln_report.dep.type = DependencyType.TRANSITIVE

        files_to_commit = self.poetry_manager.update(vuln_report)

        self.assertTrue(
            self.mock_command_runner.has_called(cmd="/usr/local/bin/poetry", args=["add", "package1@^2.0.0"])
        )
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/local/bin/poetry", args=["lock", "--no-update"]))
        self.assertEqual(files_to_commit, [str(vuln_report.lockfile.path)])

    def test_update_skips_when_fixed_version_is_none(self) -> None:
        vuln_report = self.audit_report
        vuln_report.fixed_version = None
        vuln_report.fix_skip_reason = "No fix available"

        with self.assertRaises(RuntimeError):
            self.poetry_manager.update(vuln_report)


if __name__ == "__main__":
    unittest.main()
