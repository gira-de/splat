from unittest.mock import MagicMock, patch

import requests

from splat.notifications.teams.model import TeamsPayloadContentBodyElement
from tests.notifications.base_test import BaseTestTeamsNotificationSink


class TestTeamsSendNotification(BaseTestTeamsNotificationSink):
    @patch("requests.post")
    def test_send_notification_success(self, mock_post: MagicMock) -> None:
        body_chunk = [
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                text="Test Notification",
                weight="bolder",
                size="extraLarge",
            )
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.teams_sink._send_notification(self.webhook_url, [body_chunk])

        mock_post.assert_called_once_with(
            self.webhook_url,
            json={
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "msteams": {"width": "Full"},
                            "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.5",
                            "body": [chunk.model_dump(exclude_unset=True, by_alias=True) for chunk in body_chunk],
                        },
                    }
                ],
            },
            headers={"Content-Type": "application/json"},
            timeout=5.0,
        )
        self.assertTrue(self.mock_logger.has_logged("INFO: Notification sent successfully"))

    @patch("requests.post")
    def test_send_notification_handles_timeout(self, mock_post: MagicMock) -> None:
        # Setup
        body_chunk = [
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                text="Test Notification",
                weight="bolder",
                size="extraLarge",
            )
        ]

        mock_post.side_effect = requests.Timeout  # Simulate a timeout exception

        # Act
        self.teams_sink._send_notification(self.webhook_url, [body_chunk])

        # Assert
        mock_post.assert_called_once()
        self.assertTrue(self.mock_logger.has_logged("ERROR: Failed to send Teams notification: Timeout error occurred"))

    @patch("requests.post")
    def test_send_notification_handles_http_error(self, mock_post: MagicMock) -> None:
        # Setup
        body_chunk = [
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                text="Test Notification",
                weight="bolder",
                size="extraLarge",
            )
        ]

        mock_response = MagicMock()
        mock_response.status_code = 500  # Simulate an HTTP 500 error
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP error")
        mock_post.return_value = mock_response

        # Act
        self.teams_sink._send_notification(self.webhook_url, [body_chunk])

        # Assert
        mock_post.assert_called_once()
        self.assertTrue(
            self.mock_logger.has_logged("ERROR: Failed to send Teams notification: HTTP error occurred: HTTP error")
        )

    @patch("requests.post")
    def test_send_notification_handles_request_exception(self, mock_post: MagicMock) -> None:
        # Setup
        body_chunk = [
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                text="Test Notification",
                weight="bolder",
                size="extraLarge",
            )
        ]

        mock_post.side_effect = requests.RequestException("Request failed")  # Simulate a generic request exception

        # Act
        self.teams_sink._send_notification(self.webhook_url, [body_chunk])

        # Assert
        mock_post.assert_called_once()
        self.assertTrue(
            self.mock_logger.has_logged(
                "ERROR: Failed to send Teams notification: Request error occurred: Request failed"
            )
        )
