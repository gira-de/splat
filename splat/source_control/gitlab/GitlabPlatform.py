from __future__ import annotations

from typing import List, Optional

import requests

from splat.config.model import PlatformConfig
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.source_control.gitlab.api import GitLabAPI
from splat.source_control.gitlab.model import GitLabConfig
from splat.source_control.gitlab.mr_handler import MergeRequestHandler
from splat.source_control.gitlab.projects_handler import GitlabProjectHandler
from splat.utils.env_manager.interface import EnvManager
from splat.utils.env_manager.os import OsEnvManager
from splat.utils.logger_config import default_logger


class GitlabPlatform(GitPlatformInterface):
    def __init__(
        self,
        config: GitLabConfig,
        logger: Optional[LoggerInterface] = None,
        env_manager: Optional[EnvManager] = None,
        api: Optional[GitLabAPI] = None,
    ) -> None:
        super().__init__(config)
        self.logger = logger or default_logger
        self.env_manager = env_manager or OsEnvManager(self.logger)
        self.domain = self.env_manager.resolve_value(config.domain)
        self._access_token = self.env_manager.resolve_value(config.access_token)
        self._name = config.name
        self.filters = config.filters
        self.api = api or GitLabAPI(self.domain, self._access_token)
        self.project_handler = GitlabProjectHandler(self.api, self.logger)
        self.mr_handler = MergeRequestHandler(self.api, self.logger)

    @property
    def type(self) -> str:
        return "gitlab"

    @property
    def name(self) -> str:
        return self._name

    @property
    def merge_request_type(self) -> str:
        return "Merge"

    @property
    def access_token(self) -> str:
        return self._access_token

    @classmethod
    def from_platform_config(cls, platform_config: PlatformConfig) -> GitlabPlatform:
        config_dict = platform_config.model_dump()
        validated_config = GitLabConfig.model_validate(config_dict)
        return cls(config=validated_config)

    def fetch_projects(self, project_id: Optional[str] = None, timeout: float = 60) -> List[RemoteProject]:
        if project_id:
            self.logger.info(f"Fetching project with ID '{project_id}'...")
            project = self.project_handler.fetch_project_with_id(project_id, timeout)
            return [project] if project else []
        else:
            return self.project_handler.fetch_projects(timeout)

    def create_or_update_merge_request(
        self,
        project: RemoteProject,
        commit_messages: list[str],
        branch_name: str,
        remaining_vulns: list[AuditReport],
        title: str = "Splat Dependency Updates",
    ) -> MergeRequest:
        mr_title = self.mr_handler.build_merge_request_title(remaining_vulns, title)
        try:
            open_mr = self.mr_handler.get_open_merge_request(project, branch_name)
            if open_mr:
                self.logger.info(f"Found an open merge request in project {project.name_with_namespace}")
                return self.mr_handler.update_existing_merge_request(
                    project, open_mr, mr_title, commit_messages, remaining_vulns
                )
            else:
                return self.mr_handler.create_new_merge_request(
                    project, mr_title, commit_messages, remaining_vulns, branch_name
                )
        except requests.HTTPError as e:
            action = "update" if "update_endpoint" in locals() else "create"
            error_msg = f"Failed to {action} merge request for {project.name_with_namespace}: {e}"
            self.logger.error(error_msg)
            raise e
