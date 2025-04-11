from splat.source_control.common.description_updater import DescriptionUpdater
from tests.source_control.base_test import BaseSourceControlTest


class TestDescriptionUpdater(BaseSourceControlTest):
    def setUp(self) -> None:
        super().setUp()
        self.updater = DescriptionUpdater()

        self.new_commit_messages_part = (
            "<details>\n<summary>Security: Update Package A to 1.0.0</summary>\n\n" "</details>\n\n"
        )

        self.new_remaining_vulns_part = (
            "**Remaining Vulnerable dependencies:**\n\n"
            "<details>\n<summary>New package vulnerability</summary>\n\n"
            "</details>\n\n"
        )

    def test_update_existing_description(self) -> None:
        existing_description = (
            "Initial content\n\n"
            "**Updates Summary:**\n\n"
            "Some previous updates.\n\n"
            "**Remaining Vulnerable dependencies:**\n\n"
            "Previous vulnerability details.\n"
        )

        expected_description = (
            "Initial content\n\n"
            "**Updates Summary:**\n"
            "<details>\n<summary>Security: Update Package A to 1.0.0</summary>\n\n"
            "</details>\n\n\n"
            "Some previous updates.\n\n"
            "**Remaining Vulnerable dependencies:**\n"
            "<details>\n<summary>New package vulnerability</summary>\n\n"
            "</details>\n\n"
        )

        result = self.updater.update_existing_description(
            existing_description,
            self.new_commit_messages_part,
            self.new_remaining_vulns_part,
        )

        self.assertEqual(result, expected_description)

    def test_update_existing_description_handles_empty_description(self) -> None:
        # Test with empty existing description
        existing_description = ""

        expected_description = (
            "\n\n**Updates Summary:**\n\n"
            "<details>\n<summary>Security: Update Package A to 1.0.0</summary>\n\n"
            "</details>\n\n"
            "\n\n**Remaining Vulnerable dependencies:**\n\n"
            "<details>\n<summary>New package vulnerability</summary>\n\n"
            "</details>\n\n"
        )

        result = self.updater.update_existing_description(
            existing_description,
            self.new_commit_messages_part,
            self.new_remaining_vulns_part,
        )
        self.assertEqual(result, expected_description)
