import unittest

from splat.config.model import PlatformConfig
from splat.environments.common import fetch_filtered_projects_for_platforms
from splat.model import RemoteProject
from splat.utils.logger_config import logger
from tests.mocks import MockGitPlatform


class TestFetchFilteredProjectsForPlatforms(unittest.TestCase):
    def setUp(self) -> None:
        self.projects = [
            RemoteProject(id=1, name_with_namespace="group/project1", clone_url="", default_branch="", web_url=""),
            RemoteProject(id=2, name_with_namespace="group/project2", clone_url="", default_branch="", web_url=""),
        ]
        self.platform = MockGitPlatform(config=PlatformConfig(type="mock"), projects=self.projects)

    def test_missing_platform_id(self) -> None:
        platform_without_id = MockGitPlatform(config=PlatformConfig(type="mock"), projects=self.projects)
        platform_without_id.id = None
        with self.assertLogs(logger.logger, level="INFO") as log:
            with self.assertRaises(ValueError):
                fetch_filtered_projects_for_platforms([platform_without_id])
            self.assertTrue(
                any("Platform ID missing for platform: mock. Skipping.." in record.message for record in log.records)
            )

    def test_one_platform_with_projects(self) -> None:
        result = fetch_filtered_projects_for_platforms([self.platform])
        self.assertEqual(len(result["mock_id"]), 2)

    def test_two_platforms_with_and_without_projects(self) -> None:
        platform2 = MockGitPlatform(PlatformConfig(type="mock"), [])
        platform2.id = "mock-id-2"

        result = fetch_filtered_projects_for_platforms([self.platform, platform2])
        self.assertEqual(len(result["mock_id"]), 2)
        if platform2.id:
            self.assertEqual(result[platform2.id], [])

    def test_no_platforms(self) -> None:
        with self.assertRaises(ValueError) as context:
            fetch_filtered_projects_for_platforms([])
        self.assertEqual(str(context.exception), "No source control platform was configured with an ID.")

    def test_filtered_projects(self) -> None:
        self.platform.config.filters.include = ["group/project2"]
        result = fetch_filtered_projects_for_platforms([self.platform])
        self.assertEqual(len(result["mock_id"]), 1)
        self.assertEqual(result["mock_id"][0].id, 2)


if __name__ == "__main__":
    unittest.main()
