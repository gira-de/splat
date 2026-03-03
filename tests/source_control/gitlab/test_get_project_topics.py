from requests import HTTPError, Response

from splat.source_control.gitlab.GitlabPlatform import GitlabPlatform
from tests.mocks import MockGitLabAPI
from tests.source_control.gitlab.base_test import BaseGitlabSourceControlTest


class TestGitlabProjectTopics(BaseGitlabSourceControlTest):
    def test_get_project_topics_returns_topics_when_api_returns_topic_list(self) -> None:
        fake_api = MockGitLabAPI(
            self.base_url,
            get_json_by_endpoint={f"/projects/{self.project.id}": {"topics": ["backend", "security"]}},
        )
        platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, fake_api)

        topics = platform.get_project_topics(self.project)

        self.assertEqual(topics, ["backend", "security"])

    def test_get_project_topics_returns_empty_list_when_api_errors(self) -> None:
        response = Response()
        response.status_code = 500
        response._content = b"Internal Server Error"
        fake_api = MockGitLabAPI(self.base_url, get_json_error=HTTPError(response=response))
        platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, fake_api)

        topics = platform.get_project_topics(self.project)

        self.assertEqual(topics, [])
        self.assertTrue(self.fake_logger.has_logged("failed to fetch topics for group/project"))

    def test_get_project_topics_returns_empty_list_when_topics_is_not_a_list(self) -> None:
        fake_api = MockGitLabAPI(
            self.base_url,
            get_json_by_endpoint={f"/projects/{self.project.id}": {"topics": "splat-maintainer:user"}},
        )
        platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, fake_api)

        topics = platform.get_project_topics(self.project)

        self.assertEqual(topics, [])
