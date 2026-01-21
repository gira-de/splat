from pydantic import ValidationError

from splat.model import RemoteProject
from tests.source_control.github.base_test import BaseGithubSourceControlTest


class TestGithubFetchProjects(BaseGithubSourceControlTest):
    def test_github_api_call_succeeds_returns_a_list_of_found_projects(self) -> None:
        self.mock_api._get_request_responses = [
            [  # First page
                {
                    "id": 123,
                    "full_name": "group/project1",
                    "clone_url": "https://github.com/octocat/project1.git",
                    "html_url": "https://github.com/octocat/project1",
                    "default_branch": "master",
                },
                {
                    "id": 456,
                    "full_name": "group/project2",
                    "clone_url": "https://github.com/octocat/project2.git",
                    "html_url": "https://github.com/octocat/project2",
                    "default_branch": "master",
                },
            ],
            [],  # Second page (empty indicating no more data)
        ]

        expected_projects = [
            RemoteProject(
                id=123,
                name_with_namespace="group/project1",
                clone_url="https://github.com/octocat/project1.git",
                web_url="https://github.com/octocat/project1",
                default_branch="master",
            ),
            RemoteProject(
                id=456,
                name_with_namespace="group/project2",
                clone_url="https://github.com/octocat/project2.git",
                web_url="https://github.com/octocat/project2",
                default_branch="master",
            ),
        ]

        projects = self.github_platform.fetch_projects()
        self.assertEqual(projects, expected_projects)
        self.assertTrue(self.mock_logger.has_logged("Fetching all accessible projects"))

    def test_github_api_call_handles_unexpected_response_structure(self) -> None:
        self.mock_api._get_request_responses = [
            [{"unexpected_field": "unexpected_value"}],
            [],
        ]

        expected_pydantic_logs = [
            "Validation failed for GitHub project 'N/A': "
            "Field 'id' - Field required; "
            "Field 'full_name' - Field required; "
            "Field 'clone_url' - Field required; "
            "Field 'html_url' - Field required; "
            "Field 'default_branch' - Field required"
            "\nWhile trying to parse:\n{'unexpected_field': 'unexpected_value'}"
        ]

        projects = self.github_platform.fetch_projects()

        self.assertEqual(projects, [])
        self.assertRaises(ValidationError)
        self.assertTrue(self.mock_logger.has_logged(expected_pydantic_logs))

    def test_github_fetch_projects_handles_invalid_api_response(self) -> None:
        self.mock_api._get_request_error = ValueError("Invalid JSON")

        with self.assertRaises(ValueError):
            self.github_platform.fetch_projects()
