import json
import unittest
from typing import Any
from unittest.mock import patch

from splat.notifications.teams.TeamsNotificationSink import TeamsNotificationSink
from tests.notifications.base_test import BaseTestTeamsNotificationSink


class TestTeamsCreateMergeRequestFailureNotification(BaseTestTeamsNotificationSink):
    def test_create_merge_request_failure_notification(self) -> None:
        with open(
            "tests/notifications/teams/TeamsNotificationSink/merge_request_failure_content.json",
            "r",
        ) as f:
            expected_json_body_chunks: list[list[dict[str, Any]]] = json.load(f)

        with patch.object(TeamsNotificationSink, "_send_notification") as mock_send:
            self.teams_sink.send_failure_notification(
                self.error_details, self.project, "Merge Request Creation or Update on github"
            )
            self.assert_notification_body(mock_send, expected_json_body_chunks)


if __name__ == "__main__":
    unittest.main()
