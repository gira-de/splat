from __future__ import annotations

from typing import List

from splat.config.model import PlatformConfig
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.source_control.common.maintainer_finder import find_project_maintainer
from splat.source_control.gitlab.api import GitLabAPI
from splat.source_control.gitlab.errors import MergeRequestHandlerError
from splat.source_control.gitlab.model import GitLabConfig
from splat.source_control.gitlab.mr_handler import MergeRequestHandler
from splat.source_control.gitlab.projects_handler import GitlabProjectHandler
from splat.utils.env_manager.interface import EnvManager


class GitlabPlatform(GitPlatformInterface):
    def __init__(
        self, config: GitLabConfig, logger: LoggerInterface, env_manager: EnvManager, api: GitLabAPI | None = None
    ) -> None:
        self._config = config
        self.logger = logger
        self.env_manager = env_manager
        self._domain = self.env_manager.resolve_value(config.domain)
        self._access_token = self.env_manager.resolve_value(config.access_token)
        self._name = config.name
        self.filters = config.filters
        self.api = api or GitLabAPI(self._domain, self._access_token)
        self.project_handler = GitlabProjectHandler(self.api, self.logger)
        self.mr_handler = MergeRequestHandler(self.api, self.logger)

    @property
    def config(self) -> GitLabConfig:
        return self._config

    @property
    def type(self) -> str:
        return "gitlab"

    @property
    def id(self) -> str | None:
        return self._config.id

    @property
    def name(self) -> str:
        return self._name

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def merge_request_type(self) -> str:
        return "Merge"

    @property
    def access_token(self) -> str:
        return self._access_token

    @classmethod
    def from_platform_config(
        cls, platform_config: PlatformConfig, logger: LoggerInterface, env_manager: EnvManager
    ) -> GitlabPlatform:
        config_dict = platform_config.model_dump()
        validated_config = GitLabConfig.model_validate(config_dict)
        return cls(config=validated_config, logger=logger, env_manager=env_manager)

    def fetch_projects(self, project_id: str | None = None, timeout: float = 60) -> List[RemoteProject]:
        if project_id:
            self.logger.info(f"Fetching project with ID '{project_id}'...")
            project = self.project_handler.fetch_project_with_id(project_id, timeout)
            return [project] if project else []
        else:
            return self.project_handler.fetch_projects(timeout)

    def get_open_merge_request_url(self, project: RemoteProject, branch_name: str, timeout: int = 10) -> str | None:
        open_mr = self.mr_handler.get_open_merge_request(project, branch_name)
        if not open_mr:
            return None
        return open_mr.web_url

    def create_or_update_merge_request(
        self,
        project: RemoteProject,
        commit_messages: list[str],
        branch_name: str,
        remaining_vulns: list[AuditReport],
        title: str = "Splat Dependency Updates",
    ) -> MergeRequest:
        mr_title = self.mr_handler.build_merge_request_title(remaining_vulns, title)
        maintainer = self.get_maintainer(project)
        try:
            open_mr = self.mr_handler.get_open_merge_request(project, branch_name)
            if open_mr:
                mr = self.mr_handler.update_existing_merge_request(
                    project, open_mr, mr_title, commit_messages, remaining_vulns
                )
            else:
                mr = self.mr_handler.create_new_merge_request(
                    project, mr_title, commit_messages, remaining_vulns, branch_name
                )
            if maintainer:
                self.mr_handler.assign_user_to_mr(maintainer, project, mr.number)
                mr.assignee = maintainer
            return mr
        except MergeRequestHandlerError as e:
            error_msg = f"Failed to create or update merge request for {project.name_with_namespace}: {e}"
            self.logger.error(error_msg)
            raise

    def get_project_topics(self, project: RemoteProject) -> list[str]:
        return self.project_handler.fetch_project_topics(project, timeout=10.0)

    def get_maintainer(self, project: RemoteProject) -> str | None:
        topics = self.get_project_topics(project)
        return find_project_maintainer(project.name_with_namespace, topics, self.logger)
