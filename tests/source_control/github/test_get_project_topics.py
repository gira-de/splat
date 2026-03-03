from io import BytesIO

from requests import HTTPError, Response

from tests.source_control.github.base_test import BaseGithubSourceControlTest


class TestGithubProjectTopics(BaseGithubSourceControlTest):
    def test_get_project_topics_returns_empty_list_when_api_errors(self) -> None:
        response = Response()
        response.status_code = 500
        response.raw = BytesIO(b"Internal Server Error")
        self.mock_api._get_request_error = HTTPError(response=response)

        topics = self.github_platform.get_project_topics(self.project)

        self.assertEqual(topics, [])
        self.assertTrue(self.mock_logger.has_logged("Failed to fetch topics for group/repo"))

    def test_get_project_topics_returns_empty_list_when_names_is_not_list(self) -> None:
        self.mock_api._get_request_response = {"names": "splat-maintainer:user"}

        topics = self.github_platform.get_project_topics(self.project)

        self.assertEqual(topics, [])
