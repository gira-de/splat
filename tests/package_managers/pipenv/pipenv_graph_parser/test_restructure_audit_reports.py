import unittest
from pathlib import Path

from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    VulnerabilityDetail,
)
from splat.package_managers.pipenv.pipenv_graph_parser import restructure_audit_reports


class TestRestructureAuditReports(unittest.TestCase):
    def setUp(self) -> None:
        with open("tests/package_managers/pipenv/pipenv_graph_parser/mock_pipenv_graph_output.json") as f:
            self.mock_pipenv_graph_output = f.read()

            self.direct_deps: list[Dependency] = [
                Dependency(name="package1", is_dev=True, type=DependencyType.DIRECT),
                Dependency(name="package4", is_dev=True, type=DependencyType.DIRECT),
            ]

            self.lockfile = Lockfile(
                path=Path("/path/to/project/example.lock"),
                relative_path=Path("/example.lock"),
            )

            self.mock_reports = [
                AuditReport(
                    dep=Dependency(
                        name="package3",
                        version="1.0.0",
                        type=DependencyType.TRANSITIVE,
                        is_dev=False,
                    ),
                    fixed_version="1.5.0",
                    fix_skip_reason=None,
                    vuln_details=[
                        VulnerabilityDetail(
                            id="VULN-3",
                            description="Another test vulnerability",
                            recommendation=["1.5.0"],
                            aliases=["CVE-5678"],
                        )
                    ],
                    lockfile=self.lockfile,
                ),
            ]

    def test_restructure_audit_reports_transitive_dependency(self) -> None:
        # Expected output
        expected_reports = [
            AuditReport(
                dep=Dependency(
                    name="package3",
                    version="1.0.0",
                    type=DependencyType.TRANSITIVE,
                    is_dev=False,
                ),
                fixed_version="1.5.0",
                fix_skip_reason=None,
                vuln_details=[
                    VulnerabilityDetail(
                        id="VULN-3",
                        description="Another test vulnerability",
                        recommendation=["1.5.0"],
                        aliases=["CVE-5678"],
                    )
                ],
                lockfile=self.lockfile,
            )
        ]

        # Actual output
        restructured_reports = restructure_audit_reports(
            self.mock_reports, self.mock_pipenv_graph_output, self.direct_deps
        )

        actual_parents = restructured_reports[0].dep.parent_deps
        expected_parents = expected_reports[0].dep.parent_deps

        self.assertIsNotNone(actual_parents)
        self.assertIsNotNone(expected_parents)
        if actual_parents and expected_parents:
            self.assertListEqual(actual_parents, expected_parents)

    def test_restructure_audit_reports_no_transitive_dependency(self) -> None:
        # Test when there are no transitive dependencies
        direct_report = AuditReport(
            dep=Dependency(
                name="package1",
                version="1.0.0",
                type=DependencyType.DIRECT,
                is_dev=True,
            ),
            fixed_version="2.0.0",
            fix_skip_reason=None,
            vuln_details=[
                VulnerabilityDetail(
                    id="VULN-1",
                    description="Test vulnerability",
                    recommendation=["2.0.0"],
                    aliases=["CVE-1234"],
                )
            ],
            lockfile=self.lockfile,
        )

        restructured_reports = restructure_audit_reports(
            [direct_report], self.mock_pipenv_graph_output, self.direct_deps
        )

        self.assertEqual(
            restructured_reports[0].dep.parent_deps,
            direct_report.dep.parent_deps,
        )
