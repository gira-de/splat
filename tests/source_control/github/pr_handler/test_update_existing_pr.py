from requests import HTTPError, Response

from splat.source_control.github.model import (
    GithubPullRequestEntry,
    HeadGithubPullRequestEntry,
    RepoHeadGithubPullRequestEntry,
)
from tests.source_control.github.base_test import BaseGithubSourceControlTest


class TestFindMatchingPr(BaseGithubSourceControlTest):
    def setUp(self) -> None:
        super().setUp()

    def test_update_existing_pr_successfully_updates_pr(self) -> None:
        self.setup_mock_requests_patch()

        matching_pr = GithubPullRequestEntry(
            title="Splat Dependency Updates",
            body="Some body",
            url="http://api.github.com/pulls/1",
            html_url="http://github.com/pull/1",
            head=HeadGithubPullRequestEntry(
                ref=self.branch_name, repo=RepoHeadGithubPullRequestEntry(html_url="http://github.com/repo")
            ),
        )

        result = self.github_platform.pr_handler.update_existing_pr(
            matching_pr, "Updated PR description", self.project, draft=False, timeout=30
        )

        self.assertEqual(result.title, "Splat Dependency Updates")
        self.assertEqual(result.url, "http://github.com/pull/1")
        self.assertEqual(result.project_url, "http://github.com/repo")
        self.assertEqual(result.project_name, self.project.name_with_namespace)
        self.assertEqual(result.operation, "Pull Request Updated on Github")
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    f"Updating existing pull request for {self.project.name_with_namespace}: {matching_pr.html_url}",
                    f"Pull request updated successfully for {self.project.name_with_namespace}: {matching_pr.html_url}",
                ]
            )
        )

    def test_update_existing_pr_raises_exception_on_failure(self) -> None:
        response = Response()
        response.status_code = 500
        response._content = b"Internal Server Error"
        self.mock_api._patch_request_error = HTTPError(response=response)

        matching_pr = GithubPullRequestEntry(
            title="Splat Dependency Updates",
            body="Some body",
            url="http://api.github.com/pulls/1",
            html_url="http://github.com/pull/1",
            head=HeadGithubPullRequestEntry(
                ref=self.branch_name, repo=RepoHeadGithubPullRequestEntry(html_url="http://github.com/repo")
            ),
        )

        with self.assertRaises(Exception) as context:
            self.github_platform.pr_handler.update_existing_pr(
                matching_pr,
                "Updated PR description",
                self.project,
                draft=False,
                timeout=30,
            )

        self.assertIn("Failed to update pull request", str(context.exception))
        self.assertIn("500 - Internal Server Error", str(context.exception))
