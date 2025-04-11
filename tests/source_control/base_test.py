import unittest
from pathlib import Path

from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    VulnerabilityDetail,
)


class BaseSourceControlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.commit_messages = [
            "Security: Update Package A to 1.0.0",
            "This update addresses the following vulnerabilities:",
            "Security: Update Package B to 2.0.0",
            "This update addresses the following vulnerabilities:",
        ]
        self.new_commit_messages = [
            "Security: Update Package C to 3.0.0",
            "This update addresses the following vulnerabilities:",
        ]
        self.branch_name = "splat"
        self.lockfile = Lockfile(
            path=Path("/path/to/project/example.lock"),
            relative_path=Path("/example.lock"),
        )
        self.remaining_vulns = [
            AuditReport(
                dep=Dependency(
                    name="package1",
                    version="1.0.0",
                    type=DependencyType.DIRECT,
                    is_dev=False,
                ),
                fixed_version="2.0.0",
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
                    type=DependencyType.DIRECT,
                    is_dev=True,
                ),
                fixed_version="1.5.0",
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
