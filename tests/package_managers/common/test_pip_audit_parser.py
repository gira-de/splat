import json
import unittest
from pathlib import Path

from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    Severity,
    VulnerabilityDetail,
)
from splat.package_managers.common.pip_audit_parser import parse_pip_audit_output
from tests.mocks import MockLogger


class TestPipAuditOutput(unittest.TestCase):
    def setUp(self) -> None:
        self.lockfile = Lockfile(
            path=Path("/path/to/project/example.lock"),
            relative_path=Path("/example.lock"),
        )

        with open("tests/package_managers/common/mock_pip_audit_output.json") as f:
            self.mock_pip_audit_output = f.read()

        self.direct_deps: list[Dependency] = [
            Dependency(name="package1", is_dev=False, type=DependencyType.DIRECT),
        ]

    def test_parse_pip_audit_output_with_direct_and_transitive_deps(self) -> None:
        result = parse_pip_audit_output(
            self.mock_pip_audit_output,
            self.direct_deps,
            self.lockfile,
        )

        expected_audit_report = [
            AuditReport(
                dep=Dependency(
                    name="package1",
                    version="1.0.0",
                    type=DependencyType.DIRECT,
                    is_dev=False,
                ),
                severity=Severity.UNKNOWN,
                fixed_version="2.0.0",
                fix_skip_reason=None,
                lockfile=self.lockfile,
                vuln_details=[
                    VulnerabilityDetail(
                        id="VULN-1",
                        description="Test vulnerability",
                        recommendation=["2.0.0"],
                        aliases=["CVE-1234"],
                    )
                ],
            ),
            AuditReport(
                dep=Dependency(
                    name="package2",
                    version="1.0.0",
                    type=DependencyType.TRANSITIVE,
                    is_dev=False,
                ),
                severity=Severity.UNKNOWN,
                fixed_version="1.5.0",
                fix_skip_reason=None,
                lockfile=self.lockfile,
                vuln_details=[
                    VulnerabilityDetail(
                        id="VULN-2",
                        description="Another test vulnerability",
                        recommendation=["1.5.0"],
                        aliases=["CVE-5678"],
                    )
                ],
            ),
        ]

        self.assertEqual(result, expected_audit_report)

    def test_parse_pip_audit_output_returns_empty_list_on_no_vulns(self) -> None:
        # mock output with no vulnerabilities
        mock_no_vulns_output = json.dumps(
            {
                "fixes": [],
                "dependencies": [
                    {
                        "name": "package3",
                        "version": "1.0.0",
                        "vulns": [],
                    }
                ],
            }
        )

        result = parse_pip_audit_output(
            mock_no_vulns_output,
            self.direct_deps,
            self.lockfile,
        )

        self.assertEqual(result, [])

    def test_parse_pip_audit_output_with_skip_reason(self) -> None:
        mock_no_fix_version_output = json.dumps(
            {
                "fixes": [
                    {
                        "name": "package2",
                        "old_version": "1.0.0",
                        "skip_reason": "No fix available",
                    },
                ],
                "dependencies": [
                    {
                        "name": "package2",
                        "version": "1.0.0",
                        "vulns": [
                            {
                                "id": "VULN-2",
                                "description": "Test vulnerability",
                                "fix_versions": ["None"],
                                "aliases": ["CVE-1234"],
                            }
                        ],
                    },
                ],
            }
        )
        result = parse_pip_audit_output(
            mock_no_fix_version_output,
            self.direct_deps,
            self.lockfile,
        )

        expected_direct_report = [
            AuditReport(
                dep=Dependency(
                    name="package2",
                    version="1.0.0",
                    type=DependencyType.TRANSITIVE,
                    is_dev=False,
                ),
                severity=Severity.UNKNOWN,
                fixed_version=None,
                fix_skip_reason="No fix available",  # reason
                lockfile=self.lockfile,
                vuln_details=[
                    VulnerabilityDetail(
                        id="VULN-2",
                        description="Test vulnerability",
                        recommendation=["None"],
                        aliases=["CVE-1234"],
                    )
                ],
            )
        ]

        self.assertEqual(expected_direct_report, result)

    def test_parse_pip_audit_output_handles_validation_error(self) -> None:
        mock_audit_output = "invalid json"
        mock_logger = MockLogger()
        with self.assertRaises(RuntimeError):
            parse_pip_audit_output(mock_audit_output, self.direct_deps, self.lockfile, mock_logger)
        self.assertTrue(mock_logger.has_logged("ERROR: Pip Audit output Validation Failed: Error - Invalid JSON"))


if __name__ == "__main__":
    unittest.main()
