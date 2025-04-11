from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import ValidationError

from splat.config.model import PlatformConfig
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.source_control.common.description_generator import DescriptionGenerator
from splat.source_control.common.description_updater import DescriptionUpdater
from splat.source_control.github.api import GitHubAPI
from splat.source_control.github.errors import GithubPullRequestError
from splat.source_control.github.model import GitHubConfig, GithubRepositoryEntry
from splat.source_control.github.pr_handler import GithubPRHandler
from splat.utils.env_manager.interface import EnvManager
from splat.utils.env_manager.os import OsEnvManager
from splat.utils.logger_config import default_logger
from splat.utils.logging_utils import log_pydantic_validation_error


class GithubPlatform(GitPlatformInterface):
    def __init__(
        self,
        config: GitHubConfig,
        logger: Optional[LoggerInterface] = None,
        env_manager: Optional[EnvManager] = None,
    ) -> None:
        super().__init__(config)
        self.logger = logger or default_logger
        self.env_manager = env_manager or OsEnvManager(self.logger)
        self.domain = self.env_manager.resolve_value(config.domain)
        self._access_token = self.env_manager.resolve_value(config.access_token)
        self._name = config.name
        self.filters = config.filters
        self.api = GitHubAPI(self.domain, self._access_token)
        self.description_generator = DescriptionGenerator()
        self.description_updater = DescriptionUpdater()
        self.pr_handler = GithubPRHandler(self.api, self.logger)

    @property
    def type(self) -> str:
        return "github"

    @property
    def name(self) -> str:
        return self._name

    @property
    def merge_request_type(self) -> str:
        return "Pull"

    @property
    def access_token(self) -> str:
        return self._access_token

    @classmethod
    def from_platform_config(cls, platform_config: PlatformConfig) -> GithubPlatform:
        config_dict = platform_config.model_dump()
        validated_config = GitHubConfig.model_validate(config_dict)
        return cls(config=validated_config)

    def _validate_and_create_remote_project_model(self, project_data: dict[str, Any]) -> Optional[RemoteProject]:
        try:
            proj = GithubRepositoryEntry.model_validate(project_data)
        except ValidationError as e:
            log_pydantic_validation_error(
                error=e,
                prefix_message=f"Validation failed for GitHub project '{project_data.get('full_name', 'N/A')}'",
                unparsable_data=project_data,
                logger=self.logger,
            )
            return None
        if proj.default_branch is None:
            self.logger.debug(f"Project {proj.full_name} (ID: {proj.id}) has no default branch, it will be skipped")
            return None
        return RemoteProject(
            id=proj.id,
            name_with_namespace=proj.full_name,
            clone_url=proj.clone_url,
            web_url=proj.html_url,
            default_branch=proj.default_branch,
        )

    def fetch_projects(self, project_id: Optional[str] = None, timeout: float = 60) -> list[RemoteProject]:
        """Fetches a specific repository if project_id is provided, otherwise fetches all accessible projects."""
        projects: list[RemoteProject] = []

        if project_id:
            self.logger.info(f"Fetching specific project with ID '{project_id}'...")
            endpoint = f"/repositories/{project_id}"
            response_str = self.api.get_request(endpoint)
            if response_str:
                project_data = json.loads(response_str)
                project = self._validate_and_create_remote_project_model(project_data)
                if project is None:
                    return []
                projects.append(project)
                return projects  # Return immediately since we are fetching only one project

        # Fetch all projects if no specific project ID is provided
        self.logger.info("Fetching all accessible projects")
        page = 1
        while True:
            endpoint = f"/user/repos?page={page}&per_page=100"
            response_str = self.api.get_request(endpoint)
            if not response_str:
                break

            try:
                page_content = json.loads(response_str)
            except ValueError as e:
                self.logger.error(f"Failed to decode JSON response from GitHub API: {e}")
                break

            if not page_content:
                break

            for project_data in page_content:
                project = self._validate_and_create_remote_project_model(project_data)
                if project:
                    projects.append(project)
            page += 1

        if len(projects) == 0:
            self.logger.info("No projects found.")
        return projects

    def create_or_update_merge_request(
        self,
        project: RemoteProject,
        commit_messages: list[str],
        branch_name: str,
        remaining_vulns: list[AuditReport],
        title: str = "Splat Dependency Updates",
        timeout: int = 30,
    ) -> MergeRequest:
        try:
            new_commit_messages_part = ""
            new_remaining_vulns_part = ""

            if commit_messages:
                new_commit_messages_part = self.description_generator.generate_commit_messages_description(
                    commit_messages
                )

            if remaining_vulns:
                new_remaining_vulns_part = self.description_generator.generate_remaining_vulns_description(
                    remaining_vulns
                )
                draft = True
            else:
                draft = False

            matching_pr = self.pr_handler.find_matching_pr(project, title, timeout)

            if matching_pr:
                new_pr_description = self.description_updater.update_existing_description(
                    matching_pr.body,
                    new_commit_messages_part,
                    new_remaining_vulns_part,
                )
                return self.pr_handler.update_existing_pr(matching_pr, new_pr_description, project, draft, timeout)
            else:
                new_pr_description = (
                    f"Automated pull request generated by Splat.\n\n"
                    f"**Updates Summary:**\n{new_commit_messages_part}"
                    f"{new_remaining_vulns_part}"
                )
                return self.pr_handler.create_new_pr(title, new_pr_description, branch_name, project, draft, timeout)

        except ValidationError as e:
            log_pydantic_validation_error(
                error=e,
                prefix_message=f"Merge request validation failed for {project.name_with_namespace}",
                unparsable_data=None,
                logger=self.logger,
            )
            raise e
        except GithubPullRequestError as e:
            self.logger.error(str(e))
            raise e
        except Exception as e:
            self.logger.error(f"Failed to create or update pull request for {project.name_with_namespace}: {e}")
            raise e
