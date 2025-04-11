import toml

from splat.package_managers.pipenv.PipenvPackageManager import PipenvPackageManager
from splat.utils.command_runner.interface import CommandResult
from tests.package_managers.base_test import BasePackageManagerTest


class TestPipenvAudit(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.pipenv_manager = PipenvPackageManager(
            self.mock_config, self.mock_command_runner, self.mock_fs, self.mock_logger
        )

        self.mock_pipfile_content = toml.dumps({"packages": {"package1": ">=1.0.0"}})
        self.mock_fs.write("/path/to/project/Pipfile", self.mock_pipfile_content)

    def test_pipenv_audit_installs_dependencies_runs_pip_audit_no_vulns(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/splat/.local/bin/pipenv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_no_vulns, stderr=""),
        )
        # run
        result = self.pipenv_manager.audit(self.lockfile, re_audit=False)
        # assert
        self.assertTrue(
            self.mock_command_runner.has_called(cmd="/splat/.local/bin/pipenv", args=["requirements", "--dev"])
        )
        self.assertTrue(
            self.mock_command_runner.has_called(
                cmd="/splat/.local/bin/pipenv",
                args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            )
        )
        self.assertEqual(result, [])

    def test_pipenv_audit_runs_pip_audit_returns_vulns(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/splat/.local/bin/pipenv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_with_vulns, stderr=""),
        )
        # run
        result = self.pipenv_manager.audit(self.lockfile, re_audit=False)
        self.assertEqual(result, [self.audit_report])

    def test_pipenv_audit_handles_audit_command_failure(self) -> None:
        # Setup audit command to simulate failure (non-zero exit code).
        self.mock_command_runner.set_response(
            cmd="/splat/.local/bin/pipenv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=2, stdout="", stderr="error"),
        )
        with self.assertRaises(Exception):
            # run
            self.pipenv_manager.audit(self.lockfile, re_audit=True)

    def test_pipenv_audit_with_re_audit_skips_install(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/splat/.local/bin/pipenv",
            args=["run", "pip-audit", "-r", "requirements.txt", "--fix", "-f", "json"],
            response=CommandResult(exit_code=0, stdout=self.mock_pip_audit_out_no_vulns, stderr=""),
        )
        # run
        self.pipenv_manager.audit(self.lockfile, re_audit=True)

        # Verify that install steps are skipped.
        self.assertFalse(
            self.mock_command_runner.has_called(cmd="/splat/.local/bin/pipenv", args=["install", "pip-audit", "--dev"])
        )
        self.assertFalse(
            self.mock_command_runner.has_called(cmd="/splat/.local/bin/pipenv", args=["run", "pip", "freeze"])
        )
        # Requirements command should still be executed.
        self.assertTrue(
            self.mock_command_runner.has_called(cmd="/splat/.local/bin/pipenv", args=["requirements", "--dev"])
        )
