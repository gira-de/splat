import json
import unittest

from splat.package_managers.yarn.YarnPackageManager import YarnPackageManager
from splat.utils.command_runner.interface import CommandResult
from splat.utils.errors import CommandExecutionError
from tests.package_managers.base_test import BasePackageManagerTest


class TestYarnAudit(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.yarn_manager = YarnPackageManager(self.mock_config, self.mock_ctx)

        self.mock_yarn_audit_out_no_vulns = json.dumps(
            {"advisories": [], "dependencies": [{"name": "package1", "version": "1.0.0", "vulns": []}]}
        )
        self.mock_yarn_audit_out_with_vulns = "\n".join(
            [
                json.dumps(
                    {
                        "type": "auditAdvisory",
                        "data": {
                            "resolution": {"path": "package1"},
                            "advisory": {
                                "findings": [{"version": "1.0.0", "paths": ["package1"]}],
                                "vulnerable_versions": "<2.0.0",
                                "patched_versions": ">=2.0.0",
                                "module_name": "package1",
                                "severity": "",
                                "github_advisory_id": "VULN-2",
                                "overview": "Test vulnerability",
                                "recommendation": "",
                                "cves": ["CVE-1234"],
                            },
                        },
                    }
                ),
                json.dumps({"type": "auditAdvisory"}),
            ]
        )

    def test_yarn_audit_installs_dependencies_and_runs_yarn_audit_no_vulns(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/usr/bin/yarn",
            args=["audit", "--json"],
            response=CommandResult(exit_code=0, stdout=self.mock_yarn_audit_out_no_vulns, stderr=""),
        )
        result = self.yarn_manager.audit(self.lockfile, re_audit=False)

        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["audit", "--json"]))
        self.assertEqual(result, [])

    def test_yarn_audit_installs_dependencies_and_runs_yarn_audit_with_vulns(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/usr/bin/yarn",
            args=["audit", "--json"],
            response=CommandResult(exit_code=0, stdout=self.mock_yarn_audit_out_with_vulns, stderr=""),
        )
        result = self.yarn_manager.audit(self.lockfile, re_audit=False)
        self.assertEqual(result, [self.audit_report])

    def test_yarn_audit_handles_audit_command_failure(self) -> None:
        self.mock_command_runner.set_response(
            cmd="/usr/bin/yarn",
            args=["audit", "--json"],
            response=CommandResult(exit_code=1, stdout="", stderr="Audit failed"),
        )

        with self.assertRaises(CommandExecutionError):
            self.yarn_manager.audit(self.lockfile, re_audit=True)

    def test_yarn_audit_with_re_audit_skips_install(self) -> None:
        self.yarn_manager.audit(self.lockfile, re_audit=True)

        # Verify that install step is skipped.
        self.assertFalse(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["install"]))
        self.assertTrue(self.mock_command_runner.has_called(cmd="/usr/bin/yarn", args=["audit", "--json"]))


if __name__ == "__main__":
    unittest.main()
