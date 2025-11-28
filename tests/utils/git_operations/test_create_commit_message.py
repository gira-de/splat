import unittest
from pathlib import Path

from splat.git.utils import _format_vulnerability_details, _get_severity_emoji, create_commit_message
from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    Severity,
    VulnerabilityDetail,
)


class TestCreateCommitMessage(unittest.TestCase):
    def setUp(self) -> None:
        self.lockfile = Lockfile(
            path=Path("/path/to/project/example.lock"),
            relative_path=Path("/example.lock"),
        )

    def test_get_severity_emoji(self) -> None:
        self.assertEqual(_get_severity_emoji(Severity.LOW), "🟡")
        self.assertEqual(_get_severity_emoji(Severity.MODERATE), "🟠")
        self.assertEqual(_get_severity_emoji(Severity.HIGH), "🔴")
        self.assertEqual(_get_severity_emoji(Severity.CRITICAL), "🚨")
        self.assertEqual(_get_severity_emoji(Severity.UNKNOWN), "❓")

    def test_format_vulnerability_details(self) -> None:
        vuln_detail = VulnerabilityDetail(
            id="CVE-1234",
            description="A critical security flaw.",
            recommendation=["Upgrade to version 1.0.1"],
            aliases=["CVE-1234"],
        )
        expected_details = (
            "- A critical security flaw.\n" "  - Aliases: CVE-1234\n" "  - Recommendation: Upgrade to version 1.0.1\n\n"
        )
        self.assertEqual(_format_vulnerability_details(vuln_detail), expected_details)

    def test_create_commit_message_for_direct_dependency_with_severity(self) -> None:
        dep_report = AuditReport(
            dep=Dependency(
                name="react",
                version="16.8.0",
                type=DependencyType.DIRECT,
                is_dev=True,
            ),
            severity=Severity.HIGH,
            fixed_version="16.8.6",
            vuln_details=[
                VulnerabilityDetail(
                    id="CVE-2020-1234",
                    description="Cross-site scripting vulnerability.",
                    recommendation=["Upgrade to version 16.8.6"],
                    aliases=["XXX-2020"],
                )
            ],
            lockfile=self.lockfile,
        )

        commit_message = create_commit_message(dep_report)
        expected_message = (
            "fix: Security [high 🔴]: Update react from 16.8.0 to 16.8.6 in /example.lock\n\n"
            "This update addresses the following vulnerabilities:\n\n"
            "- Cross-site scripting vulnerability.\n"
            "  - Aliases: XXX-2020\n"
            "  - Recommendation: Upgrade to version 16.8.6\n\n"
        )
        self.assertEqual(commit_message, expected_message)

    def test_create_commit_message_for_transitive_dependency_with_parents(self) -> None:
        dep_report = AuditReport(
            dep=Dependency(
                name="sample-lib",
                version="1.0.0",
                type=DependencyType.TRANSITIVE,
                parent_deps=[
                    Dependency(
                        name="parent-lib",
                        version="2",
                        type=DependencyType.TRANSITIVE,
                    )
                ],
                is_dev=False,
            ),
            severity=Severity.MODERATE,
            fixed_version="~=1.0",
            vuln_details=[
                VulnerabilityDetail(
                    id="CVE-1234",
                    description="A sample vulnerability.",
                    recommendation=["Upgrade to version 1.0.1"],
                    aliases=["CVE-1234"],
                )
            ],
            lockfile=self.lockfile,
        )

        commit_message = create_commit_message(dep_report)
        expected_message = (
            "fix: Security [moderate 🟠]: Update parent-lib to ~=2.0 to fix sample-lib "
            "in /example.lock\n\n"
            "This update addresses the following vulnerabilities:\n\n"
            "- A sample vulnerability.\n"
            "  - Aliases: CVE-1234\n"
            "  - Recommendation: Upgrade to version 1.0.1\n\n"
        )
        self.assertEqual(commit_message, expected_message)

    def test_create_commit_message_for_transitive_dependency_without_parents(
        self,
    ) -> None:
        dep_report = AuditReport(
            dep=Dependency(
                name="sample-lib",
                version="1.0.0",
                type=DependencyType.TRANSITIVE,
                parent_deps=[],
                is_dev=False,
            ),
            severity=Severity.LOW,
            fixed_version="~=1.0",
            vuln_details=[
                VulnerabilityDetail(
                    id="CVE-1234",
                    description="A sample vulnerability.",
                    recommendation=["Upgrade to version 1.0.1"],
                    aliases=["CVE-1234"],
                )
            ],
            lockfile=self.lockfile,
        )

        commit_message = create_commit_message(dep_report)
        expected_message = (
            "fix: Security [low 🟡]: Update sample-lib from 1.0.0 to ~=1.0 in /example.lock\n\n"
            "This update addresses the following vulnerabilities:\n\n"
            "- A sample vulnerability.\n"
            "  - Aliases: CVE-1234\n"
            "  - Recommendation: Upgrade to version 1.0.1\n\n"
        )
        self.assertEqual(commit_message, expected_message)

    def test_create_commit_message_for_direct_dependency_without_severity(self) -> None:
        dep_report = AuditReport(
            dep=Dependency(
                name="flask",
                version="1.1.1",
                type=DependencyType.DIRECT,
                is_dev=False,
            ),
            severity=Severity.UNKNOWN,
            fixed_version="1.1.2",
            vuln_details=[
                VulnerabilityDetail(
                    id="CVE-1234-1234",
                    description="Security fix for route handling.",
                    recommendation=["Upgrade to version 1.1.2"],
                    aliases=["XXX-ABC"],
                )
            ],
            lockfile=self.lockfile,
        )

        commit_message = create_commit_message(dep_report)
        expected_message = (
            "fix: Security: Update flask from 1.1.1 to 1.1.2 in /example.lock\n\n"
            "This update addresses the following vulnerabilities:\n\n"
            "- Security fix for route handling.\n"
            "  - Aliases: XXX-ABC\n"
            "  - Recommendation: Upgrade to version 1.1.2\n\n"
        )
        self.assertEqual(commit_message, expected_message)


if __name__ == "__main__":
    unittest.main()
