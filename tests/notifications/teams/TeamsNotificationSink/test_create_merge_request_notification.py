import json
import unittest
from typing import Any
from unittest.mock import patch

from splat.notifications.teams.TeamsNotificationSink import TeamsNotificationSink
from tests.notifications.base_test import BaseTestTeamsNotificationSink


class TestTeamsCreateMergeRequestNotification(BaseTestTeamsNotificationSink):
    def test_create_merge_request_notification_with_no_remaining_vulns(self) -> None:
        with open(
            "tests/notifications/teams/TeamsNotificationSink/merge_request_content_with_remaining_vulns.json",
            "r",
        ) as f:
            expected_json_body_chunks: list[list[dict[str, Any]]] = json.load(f)

        with patch.object(TeamsNotificationSink, "_send_notification") as mock_send:
            self.teams_sink.send_merge_request_notification(self.merge_request, self.commit_messages, [])
            self.assert_notification_body(mock_send, expected_json_body_chunks)

    def test_create_merge_request_notification_with_remaining_vulns(self) -> None:
        with open(
            "tests/notifications/teams/TeamsNotificationSink/merge_request_content_without_remaining_vulns.json",
            "r",
        ) as f:
            expected_json_body_chunks: list[list[dict[str, Any]]] = json.load(f)

        with patch.object(TeamsNotificationSink, "_send_notification") as mock_send:
            self.teams_sink.send_merge_request_notification(
                self.merge_request, self.commit_messages, self.remaining_vulns
            )
            self.assert_notification_body(mock_send, expected_json_body_chunks)

    def test_create_merge_request_notification_without_commit_messages_but_with_remaining_vulns(
        self,
    ) -> None:
        with open(
            "tests/notifications/teams/TeamsNotificationSink/merge_request_without_commits_with_remaining_vulns.json"
        ) as f:
            expected_json_body_chunks = json.load(f)

        with patch.object(TeamsNotificationSink, "_send_notification") as mock_send:
            self.teams_sink.send_merge_request_notification(self.merge_request, [], self.remaining_vulns)
            self.assert_notification_body(mock_send, expected_json_body_chunks)


if __name__ == "__main__":
    unittest.main()
