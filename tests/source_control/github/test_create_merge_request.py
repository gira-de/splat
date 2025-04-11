import unittest
from unittest.mock import MagicMock, patch

from splat.model import MergeRequest
from splat.source_control.github.pr_handler import GithubPRHandler
from tests.source_control.github.base_test import BaseGithubSourceControlTest


class TestCreateMergeRequest(BaseGithubSourceControlTest):
    def setUp(self) -> None:
        super().setUp()
        self.created_pr = MergeRequest(
            title="Splat Dependency Updates",
            url="http://github.com/pull/1",
            project_url="http://github.com/repo",
            project_name="group/repo",
            operation="Pull Request Created on Github",
        )
        self.expected_base_url = f"{self.mock_api.api_base_url}/repos/{self.project.name_with_namespace}/pulls"

    @patch("requests.post")
    @patch.object(GithubPRHandler, "find_matching_pr")
    def test_github_create_merge_request_with_commit_messages_and_no_remaining_vulns(
        self, mock_find_matching_pr: MagicMock, mock_post: MagicMock
    ) -> None:
        # Setup Mocks
        mock_find_matching_pr.return_value = None
        self.setup_mock_requests_post(mock_post)

        # Execute
        result = self.github_platform.create_or_update_merge_request(
            self.project, self.commit_messages, self.branch_name, []
        )

        # Verify
        mock_find_matching_pr.assert_called_once_with(self.project, "Splat Dependency Updates", 30)
        mock_post.assert_called_once()
        self.assertEqual(result, self.created_pr)
        self.assertTrue(
            self.mock_logger.has_logged("Pull Request created successfully for group/repo: http://github.com/pull/1")
        )

    @patch("requests.post")
    @patch.object(GithubPRHandler, "find_matching_pr")
    def test_github_create_merge_request_with_no_commit_messages_and_remaining_vulns(
        self,
        mock_find_matching_pr: MagicMock,
        mock_post: MagicMock,
    ) -> None:
        # Setup Mocks
        mock_find_matching_pr.return_value = None
        self.setup_mock_requests_post(mock_post)

        # Execute
        result = self.github_platform.create_or_update_merge_request(
            self.project, [], self.branch_name, self.remaining_vulns
        )

        # Verify
        mock_find_matching_pr.assert_called_once_with(self.project, "Splat Dependency Updates", 30)
        mock_post.assert_called_once()
        self.assertEqual(result, self.created_pr)
        self.assertTrue(
            self.mock_logger.has_logged("Pull Request created successfully for group/repo: http://github.com/pull/1")
        )

    @patch("requests.post")
    @patch.object(GithubPRHandler, "find_matching_pr")
    def test_github_create_merge_request_with_commit_messages_and_remaining_vulns(
        self, mock_find_matching_pr: MagicMock, mock_post: MagicMock
    ) -> None:
        # Setup Mocks
        mock_find_matching_pr.return_value = None
        self.setup_mock_requests_post(mock_post)

        # Execute
        result = self.github_platform.create_or_update_merge_request(
            self.project, self.commit_messages, self.branch_name, self.remaining_vulns
        )

        # Verify
        mock_find_matching_pr.assert_called_once_with(self.project, "Splat Dependency Updates", 30)
        mock_post.assert_called_once()
        self.assertEqual(result, self.created_pr)
        self.assertTrue(
            self.mock_logger.has_logged("Pull Request created successfully for group/repo: http://github.com/pull/1")
        )

    @patch("requests.post")
    @patch.object(GithubPRHandler, "find_matching_pr")
    def test_github_create_merge_request_logs_and_raises_general_exception(
        self, mock_find_matching_pr: MagicMock, mock_post: MagicMock
    ) -> None:
        # Setup Mocks
        mock_find_matching_pr.return_value = None
        mock_post.side_effect = Exception("An unexpected error occurred")

        # Execute and Verify
        with self.assertRaises(Exception):
            self.github_platform.create_or_update_merge_request(
                self.project, self.commit_messages, self.branch_name, []
            )

        self.assertTrue(
            self.mock_logger.has_logged(
                f"Failed to create or update pull request for {self.project.name_with_namespace}"
            )
        )


if __name__ == "__main__":
    unittest.main()
