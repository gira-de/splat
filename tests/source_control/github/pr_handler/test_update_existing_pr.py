from unittest.mock import MagicMock, patch

from tests.source_control.github.base_test import BaseGithubSourceControlTest


class TestFindMatchingPr(BaseGithubSourceControlTest):
    def setUp(self) -> None:
        super().setUp()

    @patch("requests.patch")
    def test_update_existing_pr_successfully_updates_pr(self, mock_patch: MagicMock) -> None:
        self.setup_mock_requests_patch(mock_patch)

        matching_pr = MagicMock()
        matching_pr.url = "http://api.github.com/pulls/1"
        matching_pr.title = "Splat Dependency Updates"
        matching_pr.html_url = "http://github.com/pull/1"
        matching_pr.head.repo.html_url = "http://github.com/repo"

        result = self.github_platform.pr_handler.update_existing_pr(
            matching_pr, "Updated PR description", self.project, draft=False, timeout=30
        )

        mock_patch.assert_called_once_with(
            url="http://api.github.com/pulls/1",
            headers=self.mock_api.headers,
            json={"body": "Updated PR description", "draft": False},
            timeout=30,
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

    @patch("requests.patch")
    def test_update_existing_pr_raises_exception_on_failure(self, mock_patch: MagicMock) -> None:
        mock_patch_response = MagicMock(status_code=500, text="Internal Server Error")
        mock_patch.return_value = mock_patch_response

        matching_pr = MagicMock()
        matching_pr.url = "http://api.github.com/pulls/1"

        with self.assertRaises(Exception) as context:
            self.github_platform.pr_handler.update_existing_pr(
                matching_pr,
                "Updated PR description",
                self.project,
                draft=False,
                timeout=30,
            )

        mock_patch.assert_called_once_with(
            url="http://api.github.com/pulls/1",
            headers=self.mock_api.headers,
            json={"body": "Updated PR description", "draft": False},
            timeout=30,
        )

        self.assertIn("Failed to update pull request", str(context.exception))
        self.assertIn("500 - Internal Server Error", str(context.exception))
