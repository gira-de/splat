from splat.interface.APIClient import JSON
from splat.source_control.gitlab.errors import MergeRequestValidationError
from splat.source_control.gitlab.GitlabPlatform import GitlabPlatform
from tests.mocks import MockGitLabAPI
from tests.source_control.gitlab.base_test import BaseGitlabSourceControlTest


class TestGitlabCreateMergeRequest(BaseGitlabSourceControlTest):
    def test_gitlab_create_merge_request_assigns_user_after_creation(self) -> None:
        valid_mr_json: JSON = {
            "id": 1,
            "iid": 101,
            "description": "Existing description",
            "state": "open",
            "source_branch": self.branch_name,
            "title": "Splat Dependency Updates",
            "web_url": "http://gitlab.com/merge_requests/101",
        }

        fake_api = MockGitLabAPI(
            self.base_url,
            get_json_by_endpoint={
                f"/projects/{self.project.id}": {"topics": ["splat-maintainer:MaintainerUser"]},
                f"/projects/{self.project.id}/merge_requests": [],
                "/users": [{"id": 77}],
            },
            post_json_response=valid_mr_json,
        )
        platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, fake_api)

        result = platform.create_or_update_merge_request(self.project, self.commit_messages, self.branch_name, [])

        self.assertEqual(result.url, "http://gitlab.com/merge_requests/101")
        self.assertEqual(result.number, 101)
        self.assertEqual(result.operation, "Merge Request Created on GitLab")
        self.assertEqual(fake_api.post_calls[0][0], f"/projects/{self.project.id}/merge_requests")
        self.assertNotIn("assignee_id", fake_api.post_calls[0][1])
        self.assertEqual(fake_api.put_calls[0][0], f"/projects/{self.project.id}/merge_requests/{result.number}")
        self.assertEqual(fake_api.put_calls[0][1], {"assignee_id": 77})

    def test_gitlab_create_merge_request_with_unresolvable_owner_logs_warning(self) -> None:
        valid_mr_json: JSON = {
            "id": 1,
            "iid": 101,
            "description": "Existing description",
            "state": "open",
            "source_branch": self.branch_name,
            "title": "Splat Dependency Updates",
            "web_url": "http://gitlab.com/merge_requests/101",
        }
        fake_api = MockGitLabAPI(
            self.base_url,
            get_json_by_endpoint={
                f"/projects/{self.project.id}": {"topics": ["splat-maintainer:MaintainerUser"]},
                f"/projects/{self.project.id}/merge_requests": [],
                "/users": [],
            },
            post_json_response=valid_mr_json,
        )
        platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, fake_api)

        result = platform.create_or_update_merge_request(self.project, self.commit_messages, self.branch_name, [])

        self.assertEqual(result.url, "http://gitlab.com/merge_requests/101")
        self.assertEqual(result.number, 101)
        self.assertEqual(result.operation, "Merge Request Created on GitLab")
        self.assertNotIn("assignee_id", fake_api.post_calls[0][1])
        self.assertEqual(len(fake_api.put_calls), 0)
        self.assertTrue(self.fake_logger.has_logged("GitLab user 'MaintainerUser' was not found for assignment"))

    def test_gitlab_create_merge_request_raises_custom_error_when_open_mr_validation_fails(self) -> None:
        fake_api = MockGitLabAPI(
            self.base_url,
            get_json_by_endpoint={
                f"/projects/{self.project.id}": {"topics": ["security"]},
                f"/projects/{self.project.id}/merge_requests": [{"invalid": "data"}],
            },
        )
        platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, fake_api)

        with self.assertRaises(MergeRequestValidationError):
            platform.create_or_update_merge_request(self.project, self.commit_messages, self.branch_name, [])

        self.assertTrue(self.fake_logger.has_logged("Failed to create or update merge request for group/project"))
