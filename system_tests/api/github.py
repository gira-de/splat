from typing import Any

import requests

from system_tests import GITHUB_API_URL, GITHUB_TOKEN


class GitHubAPI:
    def __init__(self, api_url: str = GITHUB_API_URL, token: str | None = GITHUB_TOKEN) -> None:
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def fetch_pull_request_for_branch(self, repo: str, repo_owner: str, branch_name: str) -> Any:
        url = f"{self.api_url}/repos/{repo}/pulls"
        params = {"head": f"{repo_owner}:{branch_name}"}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch PRs for repository '{repo}' and branch '{branch_name}'. "
                f"Status code: {response.status_code}, Response: {response.text}"
            )
        pull_requests = response.json()
        if not pull_requests:
            raise RuntimeError(f"No pull request found for branch '{branch_name}' in repository '{repo}'.")
        return pull_requests[0]

    def cleanup_branch_and_pull_request(self, repo: str, repo_owner: str, branch_name: str) -> None:
        self._close_pull_requests(repo, repo_owner, branch_name)
        delete_branch_url = f"{self.api_url}/repos/{repo}/git/refs/heads/{branch_name}"
        response = requests.delete(delete_branch_url, headers=self.headers)
        if response.status_code == 204:
            print(f"Successfully deleted branch '{branch_name}' from GitHub.")
        else:
            print(
                f"Failed to delete branch '{branch_name}' from GitHub: "
                f"Status code {response.status_code}, Response: {response.text}"
            )

    def _close_pull_requests(self, repo: str, repo_owner: str, branch_name: str) -> None:
        url = f"{self.api_url}/repos/{repo}/pulls"
        response = requests.get(url, headers=self.headers, params={"head": f"{repo_owner}:{branch_name}"})
        if response.status_code == 200:
            pull_requests = response.json()
            for pr in pull_requests:
                if pr["head"]["ref"] == branch_name:
                    # Close the pull request
                    pr_number = pr["number"]
                    update_pr_url = f"{self.api_url}/repos/{repo}/pulls/{pr_number}"
                    close_response = requests.patch(update_pr_url, headers=self.headers, json={"state": "closed"})
                    if close_response.status_code == 200:
                        print(f"Successfully closed pull request for branch '{branch_name}'.")
                    else:
                        print(
                            f"Failed to close pull request: Status code {close_response.status_code}, "
                            f" Response: {close_response.text}"
                        )
        else:
            print(f"Failed to fetch PRs for closing. Status code: {response.status_code}, Response: {response.text}")
