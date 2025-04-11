from typing import Dict, List, Optional, cast

import requests
from pydantic import ValidationError

from splat.interface.APIClient import JSON
from splat.interface.logger import LoggerInterface
from splat.model import RemoteProject
from splat.source_control.gitlab.api import GitLabAPI
from splat.source_control.gitlab.errors import GitlabProjectFetchError
from splat.source_control.gitlab.model import GitLabRepositoryEntry
from splat.utils.logging_utils import log_pydantic_validation_error


class GitlabProjectHandler:
    def __init__(self, api: GitLabAPI, logger: LoggerInterface) -> None:
        self.api = api
        self.logger = logger

    def _validate_and_create_remote_project_model(self, project_data: Dict[str, JSON]) -> Optional[RemoteProject]:
        try:
            proj = GitLabRepositoryEntry.model_validate(project_data)
        except ValidationError as e:
            log_pydantic_validation_error(
                error=e,
                prefix_message="Validation failed for GitLab project "
                f"'{project_data.get('path_with_namespace', 'N/A')}'",
                unparsable_data=project_data,
                logger=self.logger,
            )
            return None
        if proj.default_branch is None:
            self.logger.debug(
                f"Project {proj.path_with_namespace} (ID: {proj.id}) has no default branch, it will be skipped"
            )
            return None
        return RemoteProject(
            proj.path_with_namespace, proj.id, proj.web_url, proj.http_url_to_repo, proj.default_branch
        )

    def fetch_project_with_id(self, project_id: str, timeout: float = 60) -> Optional[RemoteProject]:
        self.logger.info(f"Fetching specific project with ID '{project_id}'...")
        endpoint = f"/projects/{project_id}"
        try:
            project_data = cast(Dict[str, JSON], self.api.get_json(endpoint))
        except requests.HTTPError as e:
            msg = f"Failed to fetch project with ID {project_id}: {e}"
            self.logger.error(msg)
            raise GitlabProjectFetchError(msg) from e
        return self._validate_and_create_remote_project_model(project_data)

    def fetch_projects(self, timeout: float = 60) -> List[RemoteProject]:
        self.logger.info("Fetching all accessible projects")
        projects: List[RemoteProject] = []
        page = 1
        per_page = 100

        while True:
            endpoint = "/projects"
            params = {"membership": "true", "archived": "false", "per_page": str(per_page), "page": str(page)}
            try:
                response = self.api.get_json(endpoint, params)
                page_content = cast(List[Dict[str, JSON]], response)
            except requests.HTTPError as e:
                msg = f"Failed to fetch projects: {e}"
                self.logger.error(msg)
                raise GitlabProjectFetchError(msg) from e

            if not page_content:
                break

            for project_data in page_content:
                project = self._validate_and_create_remote_project_model(project_data)
                if project:
                    projects.append(project)
            page += 1

        if not projects:
            self.logger.info("No projects found.")
        return projects
