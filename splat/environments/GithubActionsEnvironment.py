import json

from pydantic import BaseModel

from splat.environments.common import fetch_filtered_projects_for_platforms
from splat.interface.ExecutionEnvironmentInterface import ExecutionEnvironmentInterface
from splat.model import RemoteProject
from splat.utils.logger_config import logger


class GitHubPlatformProject(BaseModel):
    platform_id: str
    project_id: str
    project_name: str


def _generate_platform_project_list(
    platform_to_projects: dict[str, list[RemoteProject]],
) -> list[GitHubPlatformProject]:
    """Convert platform-project mappings to a list of GitHubPlatformProject model."""
    return [
        GitHubPlatformProject(
            platform_id=platform_id, project_id=str(project.id), project_name=project.name_with_namespace
        )
        for platform_id, projects in platform_to_projects.items()
        for project in projects
    ]


class GitHubActionsEnvironment(ExecutionEnvironmentInterface):
    def execute(self) -> None:
        """Fetch projects and generate a JSON file with platform and project mappings."""
        logger.info("Executing in GitHub Actions environment...")
        platform_to_projects = fetch_filtered_projects_for_platforms(self.git_platforms)
        projects_data = _generate_platform_project_list(platform_to_projects)
        # Write the JSON to a file
        json_file_path = "/splat/platform_projects.json"
        with open(json_file_path, "w") as file:
            json.dump([proj.model_dump() for proj in projects_data], file, indent=2)
        logger.info(f"Generated JSON file: {json_file_path}")
