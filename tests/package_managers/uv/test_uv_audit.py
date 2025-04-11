import unittest

import toml

from splat.package_managers.uv.UvPackageManager import UvPackageManager
from splat.utils.command_runner.interface import CommandResult
from tests.package_managers.base_test import BasePackageManagerTest


class TestUvAudit(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.uv_manager = UvPackageManager(self.mock_config, self.mock_command_runner, self.mock_fs, self.mock_logger)

        self.mock_pyproject_content = toml.dumps({"project": {"dependencies": {"package1": ">=1.0.0"}}})
        self.mock_fs.write("/path/to/project/pyproject.toml", self.mock_pyproject_content)

    def test_uv_audit_installs_dependencies_runs_pip_audit_no_vulns(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/splat/.local/bin/uv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_no_vulns, stderr=""),
        )

        result = self.uv_manager.audit(self.lockfile, re_audit=False)

        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/splat/.local/bin/uv",
                args=["export", "--no-emit-project", "--dev", "--no-hashes", "-o", "requirements.txt"],
            )
        )
        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/splat/.local/bin/uv", args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"]
            )
        )
        self.assertEqual(result, [])

    def test_poetry_audit_runs_pip_audit_returns_vulns(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/splat/.local/bin/uv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_with_vulns, stderr=""),
        )
        # run
        result = self.uv_manager.audit(self.lockfile, re_audit=False)
        # assert
        self.assertEqual(result, [self.audit_report])

    def test_uv_audit_handles_audit_command_failure(self) -> None:
        self.mock_command_runner.set_response(
            cmd="uv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=2, stdout="", stderr="Audit failed"),
        )
        with self.assertRaises(Exception):
            self.uv_manager.audit(self.lockfile, re_audit=True)

    def test_uv_audit_with_re_audit_skips_install(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/splat/.local/bin/uv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_no_vulns, stderr=""),
        )

        self.uv_manager.audit(self.lockfile, re_audit=True)

        # Verify that install steps are skipped.
        self.assertFalse(self.mock_command_runner.has_called(cmd="/splat/.local/bin/uv", args=["install"]))
        self.assertFalse(
            self.mock_command_runner.has_called(cmd="/splat/.local/bin/uv", args=["add", "pip-audit", "--dev"])
        )


if __name__ == "__main__":
    unittest.main()
