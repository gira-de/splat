import json
from typing import Optional

import requests
from pydantic import ValidationError

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

    def find_matching_pr(self, project: RemoteProject, pr_title: str, timeout: int) -> Optional[GithubPullRequestEntry]:
        response = requests.get(
            url=f"{self.api.api_base_url}/repos/{project.name_with_namespace}/pulls",
            headers=self.api.headers,
            params={"state": "open"},
            timeout=timeout,
        )

        if response.status_code == 200:
            existing_prs = response.json()
            for line in existing_prs:
                try:
                    pr = GithubPullRequestEntry.model_validate(line)
                    if pr.title == pr_title:
                        self.logger.info(f"Found an open pull request in project {project.name_with_namespace}")
                        return pr
                except ValidationError as e:
                    log_pydantic_validation_error(
                        error=e,
                        prefix_message=f"Validation Failed When fetching existing pull requests in "
                        f"{project.name_with_namespace}",
                        unparsable_data=json.dumps(line),
                        logger=self.logger,
                    )
        else:
            raise GithubPullRequestError(project.name_with_namespace, response, "fetch")
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

        # update PR
        response = requests.patch(
            url=matching_pr.url,
            headers=self.api.headers,
            json={"body": new_pr_description, "draft": draft},
            timeout=timeout,
        )
        if response.status_code == 200:
            self.logger.info(
                f"Pull request updated successfully for {project.name_with_namespace}: {matching_pr.html_url}"
            )
            return MergeRequest(
                title=matching_pr.title,
                url=matching_pr.html_url,
                project_url=matching_pr.head.repo.html_url,
                project_name=project.name_with_namespace,
                operation="Pull Request Updated on Github",
            )
        else:
            raise GithubPullRequestError(project.name_with_namespace, response, "update")

    def create_new_pr(
        self, pr_title: str, pr_description: str, branch_name: str, project: RemoteProject, draft: bool, timeout: int
    ) -> MergeRequest:
        self.logger.debug(f"Creating new pull request for {project.name_with_namespace} with title: {pr_title}")
        response = requests.post(
            url=f"{self.api.api_base_url}/repos/{project.name_with_namespace}/pulls",
            headers=self.api.headers,
            json={
                "title": pr_title,
                "body": pr_description,
                "head": branch_name,
                "base": project.default_branch,
                "draft": draft,
            },
            timeout=timeout,
        )
        if response.status_code == 201:
            pr = GithubPullRequestEntry.model_validate_json(json.dumps(response.json()))
            self.logger.info(f"Pull Request created successfully for {project.name_with_namespace}: {pr.html_url}")
            return MergeRequest(
                title=pr_title,
                url=pr.html_url,
                project_url=pr.head.repo.html_url,
                project_name=project.name_with_namespace,
                operation="Pull Request Created on Github",
            )
        else:
            raise GithubPullRequestError(project.name_with_namespace, response, "create")
