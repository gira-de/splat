from splat.model import AuditReport
from splat.source_control.common.description_generator import DescriptionGenerator
from tests.source_control.base_test import BaseSourceControlTest


class TestDescriptionGenerator(BaseSourceControlTest):
    def setUp(self) -> None:
        super().setUp()
        self.generator = DescriptionGenerator()

    def test_generate_commit_messages_description(self) -> None:
        expected_description = (
            "<details>\n"
            "<summary>Security: Update Package A to 1.0.0</summary>\n"
            "\n\n"
            "</details>\n\n"
            "<details>\n"
            "<summary>This update addresses the following vulnerabilities:</summary>\n"
            "\n\n"
            "</details>\n\n"
            "<details>\n"
            "<summary>Security: Update Package B to 2.0.0</summary>\n"
            "\n\n"
            "</details>\n\n"
            "<details>\n"
            "<summary>This update addresses the following vulnerabilities:</summary>\n"
            "\n\n"
            "</details>\n\n"
        )

        result = self.generator.generate_commit_messages_description(self.commit_messages)
        self.assertEqual(result, expected_description)

    def test_generate_remaining_vulns_description(self) -> None:
        expected_description = (
            "**Remaining Vulnerable dependencies:**\n\n"
            "These dependencies could not be resolved automatically and need manual intervention\n"
            "<details>\n"
            "<summary>package1 in /example.lock</summary>\n\n"
            "  - **Installed version**: 1.0.0\n"
            "  - **Safe version**: 2.0.0\n"
            "  - **Type of inclusion (Direct or Transitive)**: DIRECT\n"
            "  - **Found Vulnerabilities**:\n"
            "  <details>\n<summary>VULN-1</summary>\n\n"
            "  - **Vulnerability ID**: VULN-1\n\n"
            "  - **Description**: Test vulnerability\n\n"
            "  - **Recommendation**: 2.0.0\n\n"
            "  - **Aliases**: CVE-1234\n\n"
            "   </details>\n"
            "</details>\n\n"
            "<details>\n"
            "<summary>package2 in /example.lock</summary>\n\n"
            "  - **Installed version**: 1.0.0\n"
            "  - **Safe version**: 1.5.0\n"
            "  - **Type of inclusion (Direct or Transitive)**: DIRECT\n"
            "  - **Found Vulnerabilities**:\n"
            "  <details>\n<summary>VULN-2</summary>\n\n"
            "  - **Vulnerability ID**: VULN-2\n\n"
            "  - **Description**: Another test vulnerability\n\n"
            "  - **Recommendation**: 1.5.0\n\n"
            "  - **Aliases**: CVE-5678\n\n"
            "   </details>\n"
            "</details>\n\n"
        )

        result = self.generator.generate_remaining_vulns_description(self.remaining_vulns)
        self.assertEqual(result, expected_description)

    def test_generate_commit_messages_description_handles_empty_commit_list(
        self,
    ) -> None:
        commit_messages: list[str] = []
        expected_description = ""

        result = self.generator.generate_commit_messages_description(commit_messages)
        self.assertEqual(result, expected_description)

    def test_generate_remaining_vulns_description_handles_no_vulnerabilities(
        self,
    ) -> None:
        remaining_vulns: list[AuditReport] = []
        expected_description = ""

        result = self.generator.generate_remaining_vulns_description(remaining_vulns)
        self.assertEqual(result, expected_description)
