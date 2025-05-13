import unittest

import toml

from splat.package_managers.poetry.PoetryPackageManager import PoetryPackageManager
from splat.utils.command_runner.interface import CommandResult
from splat.utils.errors import CommandExecutionError
from tests.package_managers.base_test import BasePackageManagerTest


class TestPoetryAudit(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.poetry_manager = PoetryPackageManager(
            self.mock_config, self.mock_command_runner, self.mock_fs, self.mock_logger
        )

        self.mock_pyproject_content = toml.dumps({"tool": {"poetry": {"dependencies": {"package1": ">=1.0.0"}}}})
        self.mock_fs.write("/path/to/project/pyproject.toml", self.mock_pyproject_content)

    def test_poetry_audit_installs_dependencies_runs_pip_audit_no_vulns(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/usr/local/bin/poetry",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_no_vulns, stderr=""),
        )
        # run
        result = self.poetry_manager.audit(self.lockfile, re_audit=False)
        # assert
        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/usr/local/bin/poetry", args=["export", "--without-hashes", "--all-groups"]
            )
        )
        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/usr/local/bin/poetry",
                args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            )
        )
        self.assertEqual(result, [])

    def test_poetry_audit_runs_pip_audit_returns_vulns(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/usr/local/bin/poetry",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_with_vulns, stderr=""),
        )
        # run
        result = self.poetry_manager.audit(self.lockfile, re_audit=False)
        # assert
        self.assertEqual(result, [self.audit_report])

    def test_poetry_audit_handles_audit_command_failure(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/usr/local/bin/poetry",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=2, stdout="", stderr="Audit failed"),
        )

        with self.assertRaises(CommandExecutionError):
            self.poetry_manager.audit(self.lockfile, re_audit=True)

    def test_poetry_audit_with_re_audit_skips_install(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/usr/local/bin/poetry",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_no_vulns, stderr=""),
        )

        self.poetry_manager.audit(self.lockfile, re_audit=True)

        # Verify that install steps are skipped.
        self.assertFalse(self.mock_command_runner.has_called(cmd="/usr/local/bin/poetry", args=["install"]))
        self.assertFalse(
            self.mock_command_runner.has_called(cmd="/usr/local/bin/poetry", args=["add", "pip-audit", "--dev"])
        )
        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/usr/local/bin/poetry",
                args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            )
        )


if __name__ == "__main__":
    unittest.main()
