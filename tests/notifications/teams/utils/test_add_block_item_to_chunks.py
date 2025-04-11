import unittest
from unittest.mock import MagicMock, patch

from splat.notifications.teams.model import TeamsPayloadContentBodyElement
from splat.notifications.teams.utils import add_block_item_to_chunks


class TestAddBlockItemToChunks(unittest.TestCase):
    @patch("splat.notifications.teams.utils._calculate_size")
    def test_add_block_within_size_limit(self, mock_calculate_size: MagicMock) -> None:
        # Mock the size calculations
        mock_calculate_size.side_effect = [50, 30]  # current_size, block_size
        size_limit = 100

        block_item = [TeamsPayloadContentBodyElement(type="TextBlock", text="New content")]
        chunks = [[TeamsPayloadContentBodyElement(type="TextBlock", text="Existing content")]]

        result = add_block_item_to_chunks(block_item, chunks, size_limit)

        # Check that the block was added to the existing chunk
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(result[0][1].text, "New content")

    @patch("splat.notifications.teams.utils._calculate_size")
    def test_add_block_exceeds_size_limit(self, mock_calculate_size: MagicMock) -> None:
        # Mock the size calculations
        mock_calculate_size.side_effect = [80, 30]  # current_size, block_size
        size_limit = 100

        block_item = [TeamsPayloadContentBodyElement(type="TextBlock", text="New content")]
        chunks = [[TeamsPayloadContentBodyElement(type="TextBlock", text="Existing content")]]

        result = add_block_item_to_chunks(block_item, chunks, size_limit)

        # Check that a new chunk was created
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0].text, "New content")

    @patch("splat.notifications.teams.utils._calculate_size")
    def test_add_block_exactly_hits_size_limit(self, mock_calculate_size: MagicMock) -> None:
        # Mock the size calculations
        mock_calculate_size.side_effect = [70, 30]  # current_size, block_size
        size_limit = 100

        block_item = [TeamsPayloadContentBodyElement(type="TextBlock", text="New content")]
        chunks = [[TeamsPayloadContentBodyElement(type="TextBlock", text="Existing content")]]

        result = add_block_item_to_chunks(block_item, chunks, size_limit)

        # Check that the block was added to the existing chunk since it exactly hits the limit
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(result[0][1].text, "New content")

    @patch("splat.notifications.teams.utils._calculate_size")
    def test_add_block_to_empty_chunks(self, mock_calculate_size: MagicMock) -> None:
        # Mock the size calculations
        mock_calculate_size.return_value = 30  # block_size
        size_limit = 100

        block_item = [TeamsPayloadContentBodyElement(type="TextBlock", text="New content")]
        chunks: list[list[TeamsPayloadContentBodyElement]] = [[]]

        result = add_block_item_to_chunks(block_item, chunks, size_limit)

        # Check that the block was added to the empty chunk
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 1)
        self.assertEqual(result[0][0].text, "New content")


if __name__ == "__main__":
    unittest.main()
