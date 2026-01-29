from splat.model import MergeRequest
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

    def test_github_create_merge_request_with_commit_messages_and_no_remaining_vulns(self) -> None:
        # Setup Mocks
        self.mock_api._get_request_response = []
        self.setup_mock_requests_post()

        # Execute
        result = self.github_platform.create_or_update_merge_request(
            self.project, self.commit_messages, self.branch_name, []
        )

        # Verify
        self.assertEqual(result, self.created_pr)
        self.assertTrue(
            self.mock_logger.has_logged("Pull Request created successfully for group/repo: http://github.com/pull/1")
        )

    def test_github_create_merge_request_with_no_commit_messages_and_remaining_vulns(self) -> None:
        # Setup Mocks
        self.mock_api._get_request_response = []
        self.setup_mock_requests_post()

        # Execute
        result = self.github_platform.create_or_update_merge_request(
            self.project, [], self.branch_name, self.remaining_vulns
        )

        # Verify
        self.assertEqual(result, self.created_pr)
        self.assertTrue(
            self.mock_logger.has_logged("Pull Request created successfully for group/repo: http://github.com/pull/1")
        )

    def test_github_create_merge_request_with_commit_messages_and_remaining_vulns(self) -> None:
        # Setup Mocks
        self.mock_api._get_request_response = []
        self.setup_mock_requests_post()

        # Execute
        result = self.github_platform.create_or_update_merge_request(
            self.project, self.commit_messages, self.branch_name, self.remaining_vulns
        )

        # Verify
        self.assertEqual(result, self.created_pr)
        self.assertTrue(
            self.mock_logger.has_logged("Pull Request created successfully for group/repo: http://github.com/pull/1")
        )

    def test_github_create_merge_request_logs_and_raises_general_exception(self) -> None:
        # Setup Mocks
        self.mock_api._get_request_response = []
        self.mock_api._post_request_error = Exception("An unexpected error occurred")

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
