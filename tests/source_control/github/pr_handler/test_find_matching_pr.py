import unittest
from unittest.mock import MagicMock, patch

from tests.source_control.github.base_test import BaseGithubSourceControlTest


class TestFindMatchingPr(BaseGithubSourceControlTest):
    def setUp(self) -> None:
        super().setUp()

    @patch("requests.get")
    def test_find_matching_pr_returns_correct_pr_on_successful_match(self, mock_get: MagicMock) -> None:
        pr_list = [
            {
                "title": "Splat Dependency Updates",
                "body": "Some body",
                "url": "some url",
                "html_url": "http://github.com/pull/1",
                "head": {"repo": {"html_url": "url repo"}},
            },
            {
                "title": "some feature pull request",
                "body": "some body",
                "url": "some url",
                "html_url": "http://github.com/pull/2",
                "head": {"repo": {"html_url": "url repo"}},
            },
        ]
        mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=pr_list))

        matching_pr = self.github_platform.pr_handler.find_open_pr(self.project, "Splat Dependency Updates", 10)
        self.assertIsNotNone(matching_pr)
        if matching_pr:
            self.assertEqual(matching_pr.title, "Splat Dependency Updates")

        self.assertTrue(
            self.mock_logger.has_logged(
                f"INFO: Found an open pull request in project {self.project.name_with_namespace}"
            )
        )

    @patch("requests.get")
    def test_find_matching_pr_returns_none_when_no_matching_pr_found(self, mock_get: MagicMock) -> None:
        pr_list = [
            {
                "title": "some feature pull request",
                "body": "some body",
                "url": "some url",
                "html_url": "http://github.com/pull/2",
                "head": {"repo": {"html_url": "url repo"}},
            },
        ]
        mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=pr_list))

        matching_pr = self.github_platform.pr_handler.find_open_pr(self.project, self.branch_name, 10)

        self.assertIsNone(matching_pr)

    @patch("requests.get")
    def test_find_matching_pr_raises_exception_on_api_failure(self, mock_get: MagicMock) -> None:
        mock_get.return_value = MagicMock(status_code=500)

        with self.assertRaises(Exception):
            self.github_platform.pr_handler.find_open_pr(self.project, self.branch_name, 10)

    @patch("requests.get")
    def test_find_matching_pr_logs_error_on_json_validation_failure(self, mock_get: MagicMock) -> None:
        invalid_pr_list = [
            {
                "title": "Splat Dependency Updates",
                "url": "some url",
                "html_url": "http://github.com/pull/2",
                "head": {"repo": {"html_url": "url repo"}},
                # Missing required field "body"
            },
        ]
        mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=invalid_pr_list))

        self.github_platform.pr_handler.find_open_pr(self.project, self.branch_name, 10)

        self.assertTrue(
            self.mock_logger.has_logged(
                f"ERROR: Validation Failed When fetching existing pull requests in {self.project.name_with_namespace}:"
                " Field 'body' - Field required"
            )
        )


if __name__ == "__main__":
    unittest.main()
