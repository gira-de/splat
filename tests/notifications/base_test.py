import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    MergeRequest,
    RemoteProject,
    Severity,
    VulnerabilityDetail,
)
from splat.notifications.teams.model import (
    TeamsPayloadContentBodyElement,
    TeamsSinkConfig,
)
from splat.notifications.teams.TeamsNotificationSink import TeamsNotificationSink
from tests.mocks import MockEnvManager, MockLogger


class BaseTestTeamsNotificationSink(unittest.TestCase):
    def setUp(self) -> None:
        self.webhook_url = "https://example.com/webhook"
        self.mock_logger = MockLogger()
        self.mock_env_manager = MockEnvManager()
        self.teams_config = TeamsSinkConfig(type="teams", webhook_url=self.webhook_url)

        self.teams_sink = TeamsNotificationSink(self.teams_config, self.mock_logger, self.mock_env_manager)

        self.project = RemoteProject(
            default_branch="main",
            id=1,
            name_with_namespace="group/example-project",
            web_url="http://example.com/project",
            clone_url="http://example.com/project.git",
        )

        self.error_details = "An error occurred during the process."

        self.lockfile = Lockfile(
            path=Path("/path/to/project/example.lock"),
            relative_path=Path("/example.lock"),
        )

        self.dep_vuln_report = AuditReport(
            dep=Dependency(
                name="package1",
                version="2.0.0",
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
        )

        self.merge_request = MergeRequest(
            title="Splat Dependency Updates",
            url="http://example.com/merge_requests/1",
            project_url="http://example.com/project",
            project_name="example-project",
            operation="Merge Request Created",
        )

        self.commit_messages = [
            "fix: Security: Update Package A to 1.0.0",
            "fix: Security: Update Package B to 2.0.0",
        ]

        self.remaining_vulns = [
            AuditReport(
                dep=Dependency(
                    name="package1",
                    version="1.0.0",
                    type=DependencyType.DIRECT,
                    is_dev=False,
                ),
                severity=Severity.UNKNOWN,
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
        ]

    def assert_notification_body(
        self,
        mock_send: MagicMock,
        expected_json_body_chunks: list[list[dict[str, Any]]],
    ) -> None:
        actual_body_chunks: list[list[TeamsPayloadContentBodyElement]] = mock_send.call_args[0][1]
        actual_json_body_chunks = [
            [element.model_dump(exclude_unset=True, by_alias=True) for element in content_body]
            for content_body in actual_body_chunks
        ]

        self.assertEqual(actual_json_body_chunks, expected_json_body_chunks)
