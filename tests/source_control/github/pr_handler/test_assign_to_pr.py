from io import BytesIO

from requests import HTTPError, Response

from tests.source_control.github.base_test import BaseGithubSourceControlTest


class TestAssignToPr(BaseGithubSourceControlTest):
    def test_assign_user_to_pr_uses_issue_endpoint_for_assignment(self) -> None:
        self.github_platform.pr_handler.assign_user_to_pr("maintainer-user", self.project, pr_number=1)
        self.assertEqual(self.mock_api.patch_calls[0][0], "/repos/group/repo/issues/1")
        self.assertEqual(self.mock_api.patch_calls[0][1], {"assignees": ["maintainer-user"]})
        self.assertTrue(self.mock_logger.has_logged("Assigned user 'maintainer-user' to PR #1 for group/repo"))

    def test_assign_user_to_pr_logs_warning_on_http_error(self) -> None:
        response = Response()
        response.status_code = 422
        response.raw = BytesIO(b"Validation Failed")
        self.mock_api._patch_request_error = HTTPError(response=response)
        self.github_platform.pr_handler.assign_user_to_pr("maintainer-user", self.project, pr_number=1)
        self.assertEqual(len(self.mock_api.patch_calls), 1)
        self.assertTrue(
            self.mock_logger.has_logged("WARNING: Failed to assign user 'maintainer-user' to PR #1 for group/repo")
        )
