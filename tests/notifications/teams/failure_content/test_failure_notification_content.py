from unittest.mock import MagicMock, patch

from splat.notifications.teams.failure_content import (
    create_failure_notification_content,
)
from splat.notifications.teams.model import TeamsPayloadContentBodyElement
from tests.notifications.base_test import BaseTestTeamsNotificationSink


class TestCreateFailureNotificationContent(BaseTestTeamsNotificationSink):
    @patch("splat.notifications.teams.failure_content.create_toggleable_text_block")
    def test_create_failure_notification_content(self, mock_create_toggleable: MagicMock) -> None:
        # Setup
        title = "Build Failure"
        subtitle = "Error during build process"
        project_url = self.project.web_url
        error_summary = "Build failed due to unresolved dependencies."
        error_details = self.error_details

        # Mock return value for create_toggleable_text_block
        mock_create_toggleable.return_value = [
            TeamsPayloadContentBodyElement(type="TextBlock"),
            TeamsPayloadContentBodyElement(type="TextBlock"),
        ]

        # Execute
        content = create_failure_notification_content(title, subtitle, project_url, error_summary, error_details)

        # Assert
        self.assertEqual(len(content), 6)  # 4 elements + 2 from toggleable block
        self.assertIsInstance(content[0], TeamsPayloadContentBodyElement)
        self.assertEqual(content[0].text, title)
        self.assertEqual(content[1].text, subtitle)
        self.assertEqual(content[2].text, f"in [{title}]({project_url})")
        self.assertEqual(content[3].text, error_summary)

        # Ensure that the create_toggleable_text_block was called correctly
        mock_create_toggleable.assert_called_once_with(error_details, "Error Details:", 0)

    @patch("splat.notifications.teams.failure_content.create_toggleable_text_block")
    def test_empty_error_details(self, mock_create_toggleable: MagicMock) -> None:
        # Setup
        title = "Build Failure"
        subtitle = "Error during build process"
        project_url = self.project.web_url
        error_summary = "Build failed due to unresolved dependencies."
        error_details = ""  # Empty error details

        # Mock return value for create_toggleable_text_block
        mock_create_toggleable.return_value = [
            TeamsPayloadContentBodyElement(type="TextBlock"),
            TeamsPayloadContentBodyElement(type="TextBlock"),
        ]

        # Execute
        content = create_failure_notification_content(title, subtitle, project_url, error_summary, error_details)

        # Assert
        self.assertEqual(len(content), 6)  # 4 elements + 2 from toggleable block
        self.assertIsInstance(content[0], TeamsPayloadContentBodyElement)
        self.assertEqual(content[0].text, title)
        self.assertEqual(content[1].text, subtitle)
        self.assertEqual(content[2].text, f"in [{title}]({project_url})")
        self.assertEqual(content[3].text, error_summary)

        # Ensure that the create_toggleable_text_block was called correctly
        mock_create_toggleable.assert_called_once_with(error_details, "Error Details:", 0)

    @patch("splat.notifications.teams.failure_content.create_toggleable_text_block")
    def test_long_error_details(self, mock_create_toggleable: MagicMock) -> None:
        # Setup
        title = "Build Failure"
        subtitle = "Error during build process"
        project_url = self.project.web_url
        error_summary = "Build failed due to unresolved dependencies."
        error_details = "Error log:\n" + "\n".join([f"Error {i}" for i in range(100)])

        # Mock return value for create_toggleable_text_block
        mock_create_toggleable.return_value = [
            TeamsPayloadContentBodyElement(type="TextBlock"),
            TeamsPayloadContentBodyElement(type="TextBlock"),
        ]

        # Execute
        content = create_failure_notification_content(title, subtitle, project_url, error_summary, error_details)

        # Assert
        self.assertEqual(len(content), 6)  # 4 elements + 2 from toggleable block
        self.assertIsInstance(content[0], TeamsPayloadContentBodyElement)
        self.assertEqual(content[0].text, title)
        self.assertEqual(content[1].text, subtitle)
        self.assertEqual(content[2].text, f"in [{title}]({project_url})")
        self.assertEqual(content[3].text, error_summary)

        mock_create_toggleable.assert_called_once_with(error_details, "Error Details:", 0)
