import unittest

from splat.notifications.teams.model import (
    TeamsPayloadContentBodyElement,
    TeamsPayloadContentBodyElementAction,
)
from splat.notifications.teams.utils import create_toggleable_text_block


class TestTeamsCreateToggleableTextBlock(unittest.TestCase):
    def test_create_toggleable_text_block(self) -> None:
        message = "Security: Update Package A to 1.0.0"
        index = 0
        expected_output = [
            TeamsPayloadContentBodyElement(
                type="ActionSet",
                actions=[
                    TeamsPayloadContentBodyElementAction(
                        type="Action.ToggleVisibility",
                        title="Details: Security: Update Package A to 1.0.0",
                        targetElements=[{"elementId": "details_0"}],
                    )
                ],
            ),
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                id="details_0",
                isVisible=False,
                text="No additional details",
                wrap=True,
            ),
        ]

        actual_output = create_toggleable_text_block(message, "Details:", index)
        self.assertEqual(actual_output, expected_output)

    def test_create_toggleable_text_block_with_multiple_lines(self) -> None:
        message = "Security: Update Package A to 1.0.0\nFurther details on the update"
        index = 1
        expected_output = [
            TeamsPayloadContentBodyElement(
                type="ActionSet",
                actions=[
                    TeamsPayloadContentBodyElementAction(
                        type="Action.ToggleVisibility",
                        title="Info: Security: Update Package A to 1.0.0",
                        targetElements=[{"elementId": "details_1"}],
                    )
                ],
            ),
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                id="details_1",
                isVisible=False,
                text="Further details on the update",
                wrap=True,
            ),
        ]

        actual_output = create_toggleable_text_block(message, "Info:", index)
        self.assertEqual(actual_output, expected_output)


if __name__ == "__main__":
    unittest.main()
