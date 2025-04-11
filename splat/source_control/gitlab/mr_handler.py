import json
from typing import Optional, cast

from pydantic import ValidationError

from splat.interface.APIClient import JSON
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.source_control.common.description_generator import DescriptionGenerator
from splat.source_control.common.description_updater import DescriptionUpdater
from splat.source_control.gitlab.api import GitLabAPI
from splat.source_control.gitlab.errors import (
    MergeRequestCreationError,
    MergeRequestHandlerError,
    MergeRequestValidationError,
)
from splat.source_control.gitlab.model import GitLabMergeRequestEntry
from splat.utils.logging_utils import log_pydantic_validation_error


class MergeRequestHandler:
    def __init__(self, api: GitLabAPI, logger: LoggerInterface) -> None:
        self.api = api
        self.logger = logger
        self.descr_generator = DescriptionGenerator()
        self.descr_updater = DescriptionUpdater()

    def build_merge_request_title(self, remaining_vulns: list[AuditReport], title: str) -> str:
        draft_prefix = "Draft: " if remaining_vulns else ""
        return f"{draft_prefix}{title}"

    def get_open_merge_request(self, project: RemoteProject, branch_name: str) -> Optional[GitLabMergeRequestEntry]:
        mr_endpoint = f"/projects/{project.id}/merge_requests"
        params = {"state": "opened", "source_branch": branch_name}
        try:
            merge_requests_json = cast(list[JSON], self.api.get_json(mr_endpoint, params))
        except Exception as e:
            msg = f"Failed to fetch open merge requests for project {project.name_with_namespace}: {e}"
            self.logger.error(msg)
            raise MergeRequestHandlerError(msg) from e
        if not merge_requests_json:
            return None
        try:
            open_mr = GitLabMergeRequestEntry.model_validate(merge_requests_json[0])
        except ValidationError as e:
            log_pydantic_validation_error(
                error=e,
                prefix_message=f"Validation Failed When fetching existing pull requests in "
                f"{project.name_with_namespace}",
                unparsable_data=json.dumps(merge_requests_json[0]),
                logger=self.logger,
            )
            raise MergeRequestValidationError(
                f"Validation failed for open merge request in project {project.name_with_namespace}"
            ) from e

        self.logger.info(f"Found an open merge request in project {project.name_with_namespace}")
        return open_mr

    def update_existing_merge_request(
        self,
        project: RemoteProject,
        open_mr: GitLabMergeRequestEntry,
        mr_title: str,
        commit_messages: list[str],
        remaining_vulns: list[AuditReport],
    ) -> MergeRequest:
        self.logger.debug(f"Updating existing merge request for {project.name_with_namespace}: {open_mr.web_url}")
        existing_description = open_mr.description
        new_commit_messages_part = self.descr_generator.generate_commit_messages_description(commit_messages)
        remaining_vulns_part = self.descr_generator.generate_remaining_vulns_description(remaining_vulns)
        updated_description = self.descr_updater.update_existing_description(
            existing_description, new_commit_messages_part, remaining_vulns_part
        )
        update_endpoint = f"/projects/{project.id}/merge_requests/{open_mr.iid}"
        update_data: JSON = {"title": mr_title, "description": updated_description}
        try:
            updated_mr_json = cast(dict[str, JSON], self.api.put_json(update_endpoint, update_data))
        except Exception as e:
            msg = f"Failed to update merge request for project {project.name_with_namespace}: {e}"
            self.logger.error(msg)
            raise MergeRequestHandlerError(msg) from e
        try:
            gitlab_mr = GitLabMergeRequestEntry.model_validate(updated_mr_json)
        except ValidationError as e:
            error_message = f"Validation failed for updated merge request in project {project.name_with_namespace}"
            log_pydantic_validation_error(
                error=e,
                prefix_message=error_message,
                unparsable_data=json.dumps(updated_mr_json),
                logger=self.logger,
            )
            raise MergeRequestValidationError(error_message) from e
        self.logger.info(f"Merge Request updated successfully for {project.name_with_namespace}: {gitlab_mr.web_url}")
        return MergeRequest(
            title=mr_title,
            url=gitlab_mr.web_url,
            project_url=project.web_url,
            project_name=project.name_with_namespace,
            operation="Merge Request updated on GitLab",
        )

    def create_new_merge_request(
        self,
        project: RemoteProject,
        mr_title: str,
        commit_messages: list[str],
        remaining_vulns: list[AuditReport],
        branch_name: str,
    ) -> MergeRequest:
        new_commit_messages_part = self.descr_generator.generate_commit_messages_description(commit_messages)
        remaining_vulns_part = self.descr_generator.generate_remaining_vulns_description(remaining_vulns)
        mr_description = (
            "Automated merge request generated by Splat.\n\n"
            f"**Updates Summary:**\n{new_commit_messages_part}{remaining_vulns_part}"
        )
        mr_data: JSON = {
            "source_branch": branch_name,
            "target_branch": project.default_branch,
            "title": mr_title,
            "description": mr_description,
            "remove_source_branch": True,
        }
        self.logger.debug(
            f"Creating new merge request for project: {project.name_with_namespace} with title: {mr_title}"
        )
        create_endpoint = f"/projects/{project.id}/merge_requests"
        try:
            new_mr_json = cast(dict[str, JSON], self.api.post_json(create_endpoint, mr_data))
        except Exception as e:
            msg = f"Failed to create merge request for project {project.name_with_namespace}: {e}"
            self.logger.error(msg)
            raise MergeRequestCreationError(msg) from e

        try:
            gitlab_new_mr = GitLabMergeRequestEntry.model_validate(new_mr_json)
        except ValidationError as e:
            error_message = f"Validation failed for new merge request in project {project.name_with_namespace}"
            log_pydantic_validation_error(
                error=e,
                prefix_message=error_message,
                unparsable_data=json.dumps(new_mr_json),
                logger=self.logger,
            )
            raise MergeRequestValidationError(error_message) from e
        self.logger.info(
            f"Merge request created successfully for {project.name_with_namespace}: {gitlab_new_mr.web_url}"
        )
        return MergeRequest(
            title=mr_title,
            url=gitlab_new_mr.web_url,
            project_url=project.web_url,
            project_name=project.name_with_namespace,
            operation="Merge Request Created on GitLab",
        )
