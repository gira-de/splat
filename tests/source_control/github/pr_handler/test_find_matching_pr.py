from requests import HTTPError, Response

from splat.interface.APIClient import JSON
from tests.source_control.github.base_test import BaseGithubSourceControlTest


class TestFindMatchingPr(BaseGithubSourceControlTest):
    def setUp(self) -> None:
        super().setUp()

    def test_find_matching_pr_returns_correct_pr_on_successful_match(self) -> None:
        pr_list: list[JSON] = [
            {
                "title": "Splat Dependency Updates",
                "body": "Some body",
                "url": "some url",
                "html_url": "http://github.com/pull/1",
                "head": {"ref": self.branch_name, "repo": {"html_url": "url repo"}},
            },
            {
                "title": "some feature pull request",
                "body": "some body",
                "url": "some url",
                "html_url": "http://github.com/pull/2",
                "head": {"ref": "feature", "repo": {"html_url": "url repo"}},
            },
        ]
        self.mock_api._get_request_response = pr_list

        matching_pr = self.github_platform.pr_handler.find_open_pr(self.project, self.branch_name, 10)
        self.assertIsNotNone(matching_pr)
        if matching_pr:
            self.assertEqual(matching_pr.title, "Splat Dependency Updates")

        self.assertTrue(
            self.mock_logger.has_logged(
                f"INFO: Found an open pull request in project {self.project.name_with_namespace}"
            )
        )

    def test_find_matching_pr_returns_none_when_no_matching_pr_found(self) -> None:
        pr_list: list[JSON] = [
            {
                "title": "some feature pull request",
                "body": "some body",
                "url": "some url",
                "html_url": "http://github.com/pull/2",
                "head": {"ref": "feature", "repo": {"html_url": "url repo"}},
            },
        ]
        self.mock_api._get_request_response = pr_list

        matching_pr = self.github_platform.pr_handler.find_open_pr(self.project, self.branch_name, 10)

        self.assertIsNone(matching_pr)

    def test_find_matching_pr_raises_exception_on_api_failure(self) -> None:
        response = Response()
        response.status_code = 500
        response._content = b"Internal Server Error"
        self.mock_api._get_request_error = HTTPError(response=response)

        with self.assertRaises(Exception):
            self.github_platform.pr_handler.find_open_pr(self.project, self.branch_name, 10)

    def test_find_matching_pr_logs_error_on_json_validation_failure(self) -> None:
        invalid_pr_list: list[JSON] = [
            {
                "title": "Splat Dependency Updates",
                "url": "some url",
                "html_url": "http://github.com/pull/2",
                "head": {"ref": self.branch_name, "repo": {"html_url": "url repo"}},
                # Missing required field "body"
            },
        ]
        self.mock_api._get_request_response = invalid_pr_list

        self.github_platform.pr_handler.find_open_pr(self.project, self.branch_name, 10)

        self.assertTrue(
            self.mock_logger.has_logged(
                f"ERROR: Validation Failed When fetching existing pull requests in {self.project.name_with_namespace}:"
                " Field 'body' - Field required"
            )
        )
