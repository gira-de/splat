import json
from typing import cast

from pydantic import ValidationError
from requests import HTTPError

from splat.interface.APIClient import JSON
from splat.interface.logger import LoggerInterface
from splat.model import MergeRequest, RemoteProject
from splat.source_control.github.api import GitHubAPI
from splat.source_control.github.errors import GithubPullRequestError
from splat.source_control.github.model import GithubPullRequestEntry
from splat.utils.logging_utils import log_pydantic_validation_error


class GithubPRHandler:
    def __init__(self, api: GitHubAPI, logger: LoggerInterface):
        self.api = api
        self.logger = logger

    def find_matching_pr(self, project: RemoteProject, pr_title: str, timeout: int) -> GithubPullRequestEntry | None:
        try:
            response = self.api.get_json(
                endpoint=f"/repos/{project.name_with_namespace}/pulls",
                params={"state": "open"},
            )
        except HTTPError as e:
            raise GithubPullRequestError(project.name_with_namespace, e.response, "fetch")

        pulls = cast(list[JSON], response)
        for line in pulls:
            try:
                pr = GithubPullRequestEntry.model_validate(line)
                if pr.title == pr_title:
                    self.logger.info(f"Found an open pull request in project {project.name_with_namespace}")
                    return pr
            except ValidationError as e:
                log_pydantic_validation_error(
                    error=e,
                    prefix_message=(
                        "Validation Failed When fetching existing pull requests in " f"{project.name_with_namespace}"
                    ),
                    unparsable_data=json.dumps(line),
                    logger=self.logger,
                )
        return None

    def update_existing_pr(
        self,
        matching_pr: GithubPullRequestEntry,
        new_pr_description: str,
        project: RemoteProject,
        draft: bool,
        timeout: int,
    ) -> MergeRequest:
        # Update existing open PR
        self.logger.debug(f"Updating existing pull request for {project.name_with_namespace}: {matching_pr.html_url}")

        try:
            updated_pr_json = self.api.patch_request(matching_pr.url, {"body": new_pr_description, "draft": draft})
        except HTTPError as e:
            raise GithubPullRequestError(project.name_with_namespace, e.response, "update") from e

        updated_pr = GithubPullRequestEntry.model_validate(updated_pr_json)
        self.logger.info(f"Pull request updated successfully for {project.name_with_namespace}: {matching_pr.html_url}")
        return MergeRequest(
            title=updated_pr.title,
            url=updated_pr.html_url,
            project_url=updated_pr.head.repo.html_url,
            project_name=project.name_with_namespace,
            operation="Pull Request Updated on Github",
        )

    def create_new_pr(
        self, pr_title: str, pr_description: str, branch_name: str, project: RemoteProject, draft: bool, timeout: int
    ) -> MergeRequest:
        self.logger.debug(f"Creating new pull request for {project.name_with_namespace} with title: {pr_title}")
        payload: dict[str, JSON] = {
            "title": pr_title,
            "body": pr_description,
            "head": branch_name,
            "base": project.default_branch,
            "draft": draft,
        }
        try:
            pr_json = self.api.post_json(f"/repos/{project.name_with_namespace}/pulls", payload)
        except HTTPError as e:
            raise GithubPullRequestError(project.name_with_namespace, e.response, "create") from e

        pr = GithubPullRequestEntry.model_validate(pr_json)
        self.logger.info(f"Pull Request created successfully for {project.name_with_namespace}: {pr.html_url}")
        return MergeRequest(
            title=pr_title,
            url=pr.html_url,
            project_url=pr.head.repo.html_url,
            project_name=project.name_with_namespace,
            operation="Pull Request Created on Github",
        )
