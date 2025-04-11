from typing import List

from splat.interface.APIClient import JSON
from splat.model import RemoteProject
from splat.source_control.gitlab.GitlabPlatform import GitlabPlatform
from tests.mocks import MockGitLabAPI
from tests.source_control.gitlab.base_test import BaseGitlabSourceControlTest


class TestGitlabFetchProjects(BaseGitlabSourceControlTest):
    def setUp(self) -> None:
        super().setUp()

    def test_fetch_all_projects_success(self) -> None:
        # Fake responses for pagination:
        project1: JSON = {
            "id": 1,
            "path_with_namespace": "group/project1",
            "http_url_to_repo": "http://gitlab.com/project1.git",
            "web_url": "http://gitlab.com/project1",
            "default_branch": "main",
        }
        project2: JSON = {
            "id": 2,
            "path_with_namespace": "group/project2",
            "http_url_to_repo": "http://gitlab.com/project2.git",
            "web_url": "http://gitlab.com/project2",
            "default_branch": "main",
        }
        # Simulate two pages: page 1 returns two projects, page 2 returns empty list.
        fake_responses: List[JSON] = [
            [project1, project2],
            [],
        ]
        api = MockGitLabAPI(api_url=self.base_url, get_json_response=fake_responses)
        gitlab_platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, api)

        projects = gitlab_platform.fetch_projects()

        expected_projects = [
            RemoteProject(
                name_with_namespace="group/project1",
                id=1,
                clone_url="http://gitlab.com/project1.git",
                web_url="http://gitlab.com/project1",
                default_branch="main",
            ),
            RemoteProject(
                name_with_namespace="group/project2",
                id=2,
                clone_url="http://gitlab.com/project2.git",
                web_url="http://gitlab.com/project2",
                default_branch="main",
            ),
        ]
        self.assertEqual(projects, expected_projects)

    def test_fetch_specific_project_success(self) -> None:
        project_data: JSON = {
            "id": 3,
            "path_with_namespace": "group/project3",
            "http_url_to_repo": "http://gitlab.com/project3.git",
            "web_url": "http://gitlab.com/project3",
            "default_branch": "develop",
        }
        api = MockGitLabAPI(self.base_url, get_json_response=project_data)
        gitlab_platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, api)
        projects = gitlab_platform.fetch_projects(project_id="3")

        expected_projects = [
            RemoteProject(
                name_with_namespace="group/project3",
                id=3,
                clone_url="http://gitlab.com/project3.git",
                web_url="http://gitlab.com/project3",
                default_branch="develop",
            )
        ]
        self.assertEqual(projects, expected_projects)

    def test_fetch_specific_project_http_error(self) -> None:
        api = MockGitLabAPI(self.base_url, get_json_response={})
        gitlab_platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, api)
        projects = gitlab_platform.fetch_projects(project_id="4")
        self.assertEqual(projects, [])

    def test_fetch_project_without_default_branch(self) -> None:
        project_data: JSON = {
            "id": 5,
            "path_with_namespace": "group/project5",
            "http_url_to_repo": "http://gitlab.com/project5.git",
            "web_url": "http://gitlab.com/project5",
            "default_branch": None,
        }
        api = MockGitLabAPI(self.base_url, get_json_response=project_data)
        gitlab_platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, api)
        projects = gitlab_platform.fetch_projects(project_id="5")
        self.assertEqual(projects, [])  # Project should be skipped due to missing default branch

    def test_fetch_all_projects_http_error(self) -> None:
        api = MockGitLabAPI(self.base_url, get_json_response=[])
        gitlab_platform = GitlabPlatform(self.config, self.fake_logger, self.fake_env_manager, api)
        projects = gitlab_platform.fetch_projects()
        self.assertEqual(projects, [])
