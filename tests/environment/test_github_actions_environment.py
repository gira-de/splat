import unittest

from splat.environments.GithubActionsEnvironment import GitHubPlatformProject, _generate_platform_project_list
from splat.model import RemoteProject


class TestGitHubActionsExecution(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_projects = {
            "platform_1": [
                RemoteProject(
                    id=1, name_with_namespace="namespace1/project1", clone_url="", default_branch="", web_url=""
                ),
                RemoteProject(
                    name_with_namespace="namespace1/project2", id=2, clone_url="", default_branch="", web_url=""
                ),
            ],
            "platform_2": [
                RemoteProject(
                    name_with_namespace="namespace2/project3", id=3, clone_url="", default_branch="", web_url=""
                )
            ],
        }

    def test_generate_platform_project_list_base_case(self) -> None:
        result = _generate_platform_project_list(self.mock_projects)

        self.assertEqual(
            [r.model_dump() for r in result],
            [
                GitHubPlatformProject(
                    platform_id="platform_1", project_id="1", project_name="namespace1/project1"
                ).model_dump(),
                GitHubPlatformProject(
                    platform_id="platform_1", project_id="2", project_name="namespace1/project2"
                ).model_dump(),
                GitHubPlatformProject(
                    platform_id="platform_2", project_id="3", project_name="namespace2/project3"
                ).model_dump(),
            ],
        )

    def test_generate_platform_project_list_empty_input(self) -> None:
        result = _generate_platform_project_list({})
        self.assertEqual(result, [])

    def test_generate_platform_project_list_multiple_platforms_no_projects(self) -> None:
        result = _generate_platform_project_list({"platform_1": [], "platform_2": []})
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
