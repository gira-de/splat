from unittest.mock import MagicMock, patch

from splat.model import AuditReport
from splat.notifications.teams.merge_request_content import create_mr_remaning_vulns_notification_content
from splat.notifications.teams.model import TeamsPayloadContentBodyElement
from tests.notifications.base_test import BaseTestTeamsNotificationSink


class TestTeamsCreateMRremaningVulnsNotificationContent(BaseTestTeamsNotificationSink):
    @patch("splat.notifications.teams.merge_request_content.add_block_item_to_chunks")
    @patch("splat.notifications.teams.merge_request_content.create_toggleable_text_block")
    def test_teams_remaining_vulns_mr_notification_content(
        self, mock_create_toggleable: MagicMock, mock_add_block: MagicMock
    ) -> None:
        # Setup
        notification_size_limit = 1000
        initial_chunks: list[list[TeamsPayloadContentBodyElement]] = [[]]
        index_counter = 0

        # Mock the return values for the helper functions
        mock_create_toggleable.return_value = [
            TeamsPayloadContentBodyElement(type="ActionSet"),
            TeamsPayloadContentBodyElement(type="TextBlock"),
        ]
        mock_add_block.return_value = [
            [
                TeamsPayloadContentBodyElement(type="ActionSet"),
                TeamsPayloadContentBodyElement(type="TextBlock"),
            ]
        ]

        # Execute
        result_chunks = create_mr_remaning_vulns_notification_content(
            self.remaining_vulns, initial_chunks, index_counter, notification_size_limit
        )

        # Assert
        self.assertEqual(len(result_chunks), 1)  # one chunk because size is less than size limit
        self.assertIsInstance(result_chunks[0][0], TeamsPayloadContentBodyElement)
        self.assertIsInstance(result_chunks[0][1], TeamsPayloadContentBodyElement)
        self.assertEqual(mock_create_toggleable.call_count, len(self.remaining_vulns))
        self.assertEqual(mock_add_block.call_count, len(self.remaining_vulns))

        # Verify that the helper functions were called with the expected arguments
        vuln_info = (
            "package1 in /example.lock\n"
            "- **Installed version**: 1.0.0\n"
            "- **Safe version**: 2.0.0\n"
            "- **Type of inclusion (Direct or Transitive)**: DIRECT\n"
            "- **Found Vulnerabilities**:\n"
            "  - **Vulnerability ID**: VULN-1\n"
            "    - **Description**: Test vulnerability\n"
            "    - **Recommendation**: 2.0.0\n"
            "    - **Aliases**: CVE-1234\n"
        )
        mock_create_toggleable.assert_called_with(vuln_info, "", 0)

    @patch("splat.notifications.teams.merge_request_content.add_block_item_to_chunks")
    @patch("splat.notifications.teams.merge_request_content.create_toggleable_text_block")
    def test_teams_empty_remaining_vulns_mr_notification_content(
        self, mock_create_toggleable: MagicMock, mock_add_block: MagicMock
    ) -> None:
        # Setup
        notification_size_limit = 1000
        initial_chunks: list[list[TeamsPayloadContentBodyElement]] = [[]]
        index_counter = 0
        remaining_vulns: list[AuditReport] = []

        # Execute
        result_chunks = create_mr_remaning_vulns_notification_content(
            remaining_vulns, initial_chunks, index_counter, notification_size_limit
        )

        # Assert
        self.assertEqual(len(result_chunks), 1)
        self.assertEqual(len(result_chunks[0]), 0)  # should return empty
        self.assertEqual(mock_create_toggleable.call_count, 0)
        self.assertEqual(mock_add_block.call_count, 0)
