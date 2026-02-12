import unittest

from splat.environments.GitlabCIEnvironment import (
    Artifacts,
    Default,
    DockerConfig,
    ImageConfig,
    Job,
    Rule,
    _generate_pipeline,
)
from splat.model import RemoteProject
from tests.mocks import MockLogger


class TestGitLabCIExecution(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = MockLogger()
        self.project1 = RemoteProject(
            name_with_namespace="namespace1/project1", id=1, clone_url="", default_branch="", web_url=""
        )
        self.project2 = RemoteProject(
            name_with_namespace="namespace1/project2", id=2, clone_url="", default_branch="", web_url=""
        )
        self.project3 = RemoteProject(
            name_with_namespace="namespace2/project3", id=3, clone_url="", default_branch="", web_url=""
        )

    def test_generate_pipeline_one_platform_one_project(self) -> None:
        platform_to_projects = {"platform1": [self.project1]}
        pipeline = _generate_pipeline(platform_to_projects, self.logger)

        self.assertEqual(
            pipeline.default.model_dump(),
            Default(
                image=ImageConfig(
                    name="${DEFAULT_SPLAT_IMAGE}", pull_policy="always", docker=DockerConfig(user="splatuser")
                )
            ).model_dump(),
        )

        self.assertEqual(
            pipeline.__pydantic_extra__["process_namespace1/project1"].model_dump(),
            Job(
                script=["splat --platform-id platform1 --project-id 1"],
                needs=None,
                artifacts=Artifacts(paths=["dashboard/"]),
                rules=[Rule(when="on_success")],
            ).model_dump(),
        )

        self.assertEqual(
            pipeline.aggregate_summaries.model_dump() if pipeline.aggregate_summaries is not None else None,
            Job(
                script=[
                    "python3 /splat/aggregate_summaries.py --input-dir dashboard "
                    "--output-file dashboard/projects_summary.json"
                ],
                needs=["process_namespace1/project1"],
                artifacts=Artifacts(paths=["dashboard/projects_summary.json"]),
                rules=[Rule(when="on_success")],
            ).model_dump(),
        )

    def test_generate_pipeline_platform_without_projects(self) -> None:
        platform_to_projects: dict[str, list[RemoteProject]] = {"platform1": []}
        pipeline = _generate_pipeline(platform_to_projects, self.logger)

        self.assertEqual(len(pipeline.__pydantic_extra__), 0)
        self.assertIsNone(pipeline.aggregate_summaries)

    def test_generate_pipeline_no_platforms(self) -> None:
        platform_to_projects: dict[str, list[RemoteProject]] = {}
        pipeline = _generate_pipeline(platform_to_projects, self.logger)

        self.assertEqual(len(pipeline.__pydantic_extra__), 0)
        self.assertIsNone(pipeline.aggregate_summaries)

    def test_generate_pipeline_multiple_platforms_multiple_projects(self) -> None:
        platform_to_projects = {
            "platform1": [self.project1, self.project2],
            "platform2": [self.project3],
        }
        pipeline = _generate_pipeline(platform_to_projects, self.logger)

        self.assertEqual(
            pipeline.default.model_dump(),
            Default(
                image=ImageConfig(
                    name="${DEFAULT_SPLAT_IMAGE}", pull_policy="always", docker=DockerConfig(user="splatuser")
                )
            ).model_dump(),
        )

        self.assertEqual(
            pipeline.__pydantic_extra__["process_namespace1/project1"].model_dump(),
            Job(
                script=["splat --platform-id platform1 --project-id 1"],
                needs=None,
                artifacts=Artifacts(paths=["dashboard/"]),
                rules=[Rule(when="on_success")],
            ).model_dump(),
        )

        self.assertEqual(
            pipeline.__pydantic_extra__["process_namespace1/project2"].model_dump(),
            Job(
                script=["splat --platform-id platform1 --project-id 2"],
                needs=None,
                artifacts=Artifacts(paths=["dashboard/"]),
                rules=[Rule(when="on_success")],
            ).model_dump(),
        )

        self.assertEqual(
            pipeline.__pydantic_extra__["process_namespace2/project3"].model_dump(),
            Job(
                script=["splat --platform-id platform2 --project-id 3"],
                needs=None,
                artifacts=Artifacts(paths=["dashboard/"]),
                rules=[Rule(when="on_success")],
            ).model_dump(),
        )

        self.assertEqual(
            pipeline.aggregate_summaries.model_dump() if pipeline.aggregate_summaries is not None else None,
            Job(
                script=[
                    "python3 /splat/aggregate_summaries.py --input-dir dashboard "
                    "--output-file dashboard/projects_summary.json"
                ],
                needs=[
                    "process_namespace1/project1",
                    "process_namespace1/project2",
                    "process_namespace2/project3",
                ],
                artifacts=Artifacts(paths=["dashboard/projects_summary.json"]),
                rules=[Rule(when="on_success")],
            ).model_dump(),
        )


if __name__ == "__main__":
    unittest.main()
