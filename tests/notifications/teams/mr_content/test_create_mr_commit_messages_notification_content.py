import unittest
from unittest.mock import MagicMock, patch

from splat.notifications.teams.merge_request_content import create_mr_commit_messages_notification_content
from splat.notifications.teams.model import TeamsPayloadContentBodyElement


class TestTeamsCreateMRCommitMessagesNotificationContent(unittest.TestCase):
    @patch("splat.notifications.teams.utils.add_block_item_to_chunks")
    @patch("splat.notifications.teams.utils.create_toggleable_text_block")
    def test_teams_create_mr_commit_messages_notification_content(
        self, mock_create_toggleable: MagicMock, mock_add_block: MagicMock
    ) -> None:
        commit_messages = ["fix: update package A", "feat: add new feature"]
        notification_size_limit = 1000

        # Mock return values focusing on structure
        mock_create_toggleable.return_value = [
            TeamsPayloadContentBodyElement(type="whatever"),
            TeamsPayloadContentBodyElement(type="whatever"),
        ]
        mock_add_block.return_value = [
            [
                TeamsPayloadContentBodyElement(type="whatever"),
                TeamsPayloadContentBodyElement(type="whatever"),
            ]
        ]

        initial_chunks: list[list[TeamsPayloadContentBodyElement]] = [[]]

        result_chunks = create_mr_commit_messages_notification_content(
            commit_messages, initial_chunks, notification_size_limit
        )

        self.assertEqual(len(result_chunks), 1)
        self.assertEqual(len(result_chunks[0]), 4)
        self.assertIsInstance(result_chunks[0][0], TeamsPayloadContentBodyElement)
        self.assertIsInstance(result_chunks[0][1], TeamsPayloadContentBodyElement)

    @patch("splat.notifications.teams.utils.add_block_item_to_chunks")
    @patch("splat.notifications.teams.utils.create_toggleable_text_block")
    def test_teams_mr_empty_commit_messages(self, mock_create_toggleable: MagicMock, mock_add_block: MagicMock) -> None:
        # Setup
        commit_messages: list[str] = []
        notification_size_limit = 1000
        initial_chunks: list[list[TeamsPayloadContentBodyElement]] = [[]]

        # Execute
        result_chunks = create_mr_commit_messages_notification_content(
            commit_messages, initial_chunks, notification_size_limit
        )

        # Assert
        self.assertEqual(result_chunks, initial_chunks)
        mock_create_toggleable.assert_not_called()
        mock_add_block.assert_not_called()


if __name__ == "__main__":
    unittest.main()
