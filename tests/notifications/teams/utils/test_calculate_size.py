import unittest

from splat.notifications.teams.model import TeamsPayloadContentBodyElement
from splat.notifications.teams.utils import _calculate_size


class TestCalculateSize(unittest.TestCase):
    def test_calculate_size_with_a_simple_content_element(self) -> None:
        content = [TeamsPayloadContentBodyElement(type="TextBlock", text="Test content")]
        size = _calculate_size(content)
        expected_size = len(content[0].model_dump_json(exclude_unset=True).encode("utf-8"))

        self.assertEqual(size, expected_size)

    def test_calculate_size_multiple_elements(self) -> None:
        content = [
            TeamsPayloadContentBodyElement(type="TextBlock", text="Test content"),
            TeamsPayloadContentBodyElement(type="TextBlock", text="More content"),
        ]
        size = _calculate_size(content)
        expected_size = sum(len(element.model_dump_json(exclude_unset=True).encode("utf-8")) for element in content)

        self.assertEqual(size, expected_size)


if __name__ == "__main__":
    unittest.main()
