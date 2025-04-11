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
from splat.package_managers.yarn.audit_parser import parse_yarn_audit_output
from tests.mocks import MockLogger


class TestYarnParseYarnAuditOutput(unittest.TestCase):
    def setUp(self) -> None:
        self.lockfile = Lockfile(
            path=Path("/path/to/project/example.lock"),
            relative_path=Path("/example.lock"),
        )

    def test_yarn_parse_yarn_audit_output_with_direct_type_deps(self) -> None:
        with open("tests/package_managers/yarn/mock_audit_output_direct_type.json", "r") as f:
            output_json = json.load(f)

        mock_audit_output = "\n".join(json.dumps(row) for row in output_json)

        expected_vulnerability_report = [
            AuditReport(
                dep=Dependency(
                    name="package1",
                    version="1.0.0",
                    type=DependencyType.DIRECT,
                ),
                severity=Severity.MODERATE,
                fixed_version="2.0.0",
                lockfile=self.lockfile,
                vuln_details=[
                    VulnerabilityDetail(
                        id="XXXX-abcd-1234-eeeE",
                        description="Some vulnerability description here",
                        recommendation=["Upgrade to version 2.0.0 or later"],
                        aliases=["CVE-123-456"],
                    )
                ],
            ),
        ]

        vulnerabilities = parse_yarn_audit_output(mock_audit_output, self.lockfile)
        self.assertEqual(vulnerabilities, expected_vulnerability_report)

    def test_yarn_parse_yarn_audit_output_with_transitive_type_deps(self) -> None:
        with open("tests/package_managers/yarn/mock_audit_output_transitive_type.json", "r") as f:
            output_json = json.load(f)

        mock_audit_output = "\n".join(json.dumps(row) for row in output_json)
        expected_vulnerability_report = [
            AuditReport(
                dep=Dependency(
                    name="package2",
                    version="1.0.0",
                    type=DependencyType.TRANSITIVE,
                ),
                severity=Severity.HIGH,
                fixed_version="2.5.0",
                lockfile=self.lockfile,
                vuln_details=[
                    VulnerabilityDetail(
                        id="abcd-1234-eeeE-XXXX",
                        description="Some vulnerability description here as well",
                        recommendation=["Upgrade to version 2.5.0 or later"],
                        aliases=["CVE-123-456"],
                    )
                ],
            ),
        ]

        vulnerabilities = parse_yarn_audit_output(mock_audit_output, self.lockfile)
        self.assertEqual(vulnerabilities, expected_vulnerability_report)

    def test_yarn_parse_yarn_audit_output_with_both_type_deps(self) -> None:
        with open("tests/package_managers/yarn/mock_audit_output_both_types.json") as f:
            output_json = json.load(f)
        mock_audit_output = "\n".join(json.dumps(row) for row in output_json)

        expected_vulnerability_report = [
            AuditReport(
                dep=Dependency(
                    name="package1",
                    version="1.0.0",
                    type=DependencyType.BOTH,
                ),
                severity=Severity.MODERATE,
                fixed_version="2.0.0",
                lockfile=self.lockfile,
                vuln_details=[
                    VulnerabilityDetail(
                        id="XXXX-abcd-1234-eeeE",
                        description="Some vulnerability description here as well",
                        recommendation=["Upgrade to version 2.0.0 or later"],
                        aliases=["CVE-123-456"],
                    )
                ],
            ),
        ]

        vulnerabilities = parse_yarn_audit_output(mock_audit_output, self.lockfile)
        self.assertEqual(vulnerabilities, expected_vulnerability_report)

    def test_parse_yarn_audit_output_returns_empty_list_on_no_vulns(self) -> None:
        mock_audit_output = json.dumps(
            [
                {
                    "type": "auditAdvisory",
                    "data": {
                        "advisory": {
                            "module_name": "package1",
                            "findings": [
                                {
                                    "version": "1.0.0",
                                    "paths": [],
                                }
                            ],
                            "vulnerabilities": [],
                        },
                        "resolution": {
                            "id": "1234",
                            "path": "package1",
                        },
                    },
                }
            ]
        )

        vulnerabilities = parse_yarn_audit_output(mock_audit_output, self.lockfile)
        self.assertEqual(vulnerabilities, [])

    def test_yarn_parse_yarn_audit_output_handles_validation_error(self) -> None:
        mock_audit_output = "{invalid json} \n {invalid json}"
        mock_logger = MockLogger()

        with self.assertRaises(RuntimeError):
            result = parse_yarn_audit_output(mock_audit_output, self.lockfile, mock_logger)
            self.assertEqual(result, [])
        self.assertTrue(mock_logger.has_logged("ERROR: Yarn Audit output Validation Failed at line {invalid json}"))


if __name__ == "__main__":
    unittest.main()
