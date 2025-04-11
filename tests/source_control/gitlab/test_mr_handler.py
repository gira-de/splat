import unittest

from splat.interface.APIClient import JSON
from splat.model import MergeRequest
from splat.source_control.gitlab.errors import MergeRequestValidationError
from splat.source_control.gitlab.model import GitLabMergeRequestEntry
from splat.source_control.gitlab.mr_handler import MergeRequestHandler
from tests.mocks.mock_gitlab_api import MockGitLabAPI
from tests.source_control.gitlab.base_test import BaseGitlabSourceControlTest


class TestGitlabMRHandler(BaseGitlabSourceControlTest):
    def setUp(self) -> None:
        super().setUp()
        self.mr_handler = MergeRequestHandler(self.gitlab_platform.api, self.fake_logger)
        # Fake JSON representing a valid open merge request.
        self.valid_mr_json: JSON = {
            "id": 1,
            "iid": 101,
            "description": "Existing description",
            "state": "open",
            "source_branch": self.branch_name,
            "title": "title",
            "web_url": "http://gitlab.com/merge_requests/101",
        }

    def test_build_merge_request_title_without_vulns(self) -> None:
        # title building when no vulnerabilities are present.
        title = self.mr_handler.build_merge_request_title([], "Splat Dependency Updates")
        self.assertEqual(title, "Splat Dependency Updates")

    def test_build_merge_request_title_with_vulns(self) -> None:
        # When vulnerabilities exist, the title should be prefixed with "Draft: ".
        title = self.mr_handler.build_merge_request_title(self.remaining_vulns, "Splat Dependency Updates")
        self.assertEqual(title, "Draft: Splat Dependency Updates")

    def test_get_open_merge_request_returns_none_when_empty(self) -> None:
        # API returns an empty list so no open MR exists.
        fake_api = MockGitLabAPI(self.base_url, get_json_response=[])
        handler = MergeRequestHandler(fake_api, self.fake_logger)
        result = handler.get_open_merge_request(self.project, self.branch_name)
        self.assertIsNone(result)

    def test_get_open_merge_request_returns_valid_mr(self) -> None:
        fake_api = MockGitLabAPI(self.base_url, get_json_response=[self.valid_mr_json])
        handler = MergeRequestHandler(fake_api, self.fake_logger)
        result = handler.get_open_merge_request(self.project, self.branch_name)
        expected_mr = GitLabMergeRequestEntry(
            id=1,
            iid=101,
            description="Existing description",
            state="open",
            source_branch=self.branch_name,
            title="title",
            web_url="http://gitlab.com/merge_requests/101",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_mr)

    def test_get_open_merge_request_raises_validation_error(self) -> None:
        invalid_mr_json: JSON = {"invalid": "data"}
        fake_api = MockGitLabAPI(self.base_url, get_json_response=[invalid_mr_json])
        handler = MergeRequestHandler(fake_api, self.fake_logger)
        with self.assertRaises(MergeRequestValidationError):
            handler.get_open_merge_request(self.project, self.branch_name)

    def test_update_existing_merge_request_success(self) -> None:
        open_mr = GitLabMergeRequestEntry.model_validate(self.valid_mr_json)
        updated_mr_json: JSON = {
            "id": 10,
            "iid": 202,
            "description": "Updated description",
            "state": "open",
            "source_branch": self.branch_name,
            "title": "Splat Dependency Updates",
            "web_url": "http://gitlab.com/merge_requests/202",
        }
        fake_api = MockGitLabAPI(self.base_url, put_json_response=updated_mr_json)
        handler = MergeRequestHandler(fake_api, self.fake_logger)
        mr_title = "Splat Dependency Updates"
        result = handler.update_existing_merge_request(
            self.project, open_mr, mr_title, self.commit_messages, self.remaining_vulns
        )
        expected_mr = MergeRequest(
            title=mr_title,
            url="http://gitlab.com/merge_requests/202",
            project_url=self.project.web_url,
            project_name=self.project.name_with_namespace,
            operation="Merge Request updated on GitLab",
        )
        self.assertEqual(result, expected_mr)

    @unittest.skip("Exception handling in MockGitlabApi not implemented")
    def test_update_existing_merge_request_failure_in_put(self) -> None:
        pass

    def test_create_new_merge_request_success(self) -> None:
        fake_api = MockGitLabAPI(self.base_url, post_json_response=self.valid_mr_json)
        handler = MergeRequestHandler(fake_api, self.fake_logger)
        mr_title = "Splat Dependency Updates"
        result = handler.create_new_merge_request(
            self.project, mr_title, self.commit_messages, self.remaining_vulns, self.branch_name
        )
        expected_mr = MergeRequest(
            title=mr_title,
            url="http://gitlab.com/merge_requests/101",
            project_url=self.project.web_url,
            project_name=self.project.name_with_namespace,
            operation="Merge Request Created on GitLab",
        )
        self.assertEqual(result, expected_mr)

    @unittest.skip("Exception handling in MockGitlabApi not implemented")
    def test_create_new_merge_request_failure_in_post(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
