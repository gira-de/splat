import unittest

from splat.model import DependencyType
from splat.package_managers.uv.UvPackageManager import UvPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestUvUpdate(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.uv_manager = UvPackageManager(self.mock_config, self.mock_command_runner, self.mock_fs, self.mock_logger)

    def test_update_direct_dependency(self) -> None:
        vuln_report = self.audit_report

        files_to_commit = self.uv_manager.update(vuln_report)
        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/usr/local/bin/uv",
                args=["add", "package1~=2.0.0"],
            )
        )
        self.assertEqual(
            files_to_commit,
            [
                str(vuln_report.lockfile.path),
                str(vuln_report.lockfile.path.parent / self.uv_manager.manifest_file_name),
            ],
        )

    def test_update_transitive_dependency(self) -> None:
        vuln_report = self.audit_report
        vuln_report.dep.type = DependencyType.TRANSITIVE

        files_to_commit = self.uv_manager.update(vuln_report)

        self.assertEqual(
            files_to_commit,
            [
                str(vuln_report.lockfile.path),
                str(vuln_report.lockfile.path.parent / self.uv_manager.manifest_file_name),
            ],
        )
        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/usr/local/bin/uv",
                args=["lock", "--upgrade-package", "package1~=2.0.0"],
            )
        )

    def test_update_skips_when_fixed_version_is_none(self) -> None:
        vuln_report = self.audit_report
        vuln_report.fixed_version = None
        vuln_report.fix_skip_reason = "No fix available"

        with self.assertRaises(RuntimeError):
            self.uv_manager.update(vuln_report)


if __name__ == "__main__":
    unittest.main()
