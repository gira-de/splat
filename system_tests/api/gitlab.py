from typing import Any, Optional
from urllib.parse import quote

import requests

from system_tests import GITLAB_API_URL, GITLAB_TOKEN


class GitLabAPI:
    def __init__(self, api_url: str = GITLAB_API_URL, token: Optional[str] = GITLAB_TOKEN) -> None:
        self.api_url = api_url
        self.headers = {"PRIVATE-TOKEN": token}

    def fetch_merge_request_for_branch(self, project_name: str, branch_name: str) -> Any:
        project_id = quote(project_name, safe="")
        url = f"{self.api_url}/projects/{project_id}/merge_requests"
        params = {"source_branch": branch_name}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch MRs for project '{project_name}' and branch '{branch_name}'. "
                f"Status code: {response.status_code}, Response: {response.text}"
            )
        merge_requests = response.json()
        if not merge_requests:
            raise RuntimeError(f"No merge request found for branch '{branch_name}' in project '{project_name}'.")
        return merge_requests[0]

    def cleanup_branch_and_merge_request(self, project_name: str, branch_name: str) -> None:
        project_id = quote(project_name, safe="")
        self._delete_merge_requests(project_id, branch_name)
        delete_branch_url = f"{self.api_url}/projects/{project_id}/repository/branches/{branch_name}"
        response = requests.delete(delete_branch_url, headers=self.headers)
        if response.status_code == 204:
            print(f"Successfully deleted branch '{branch_name}' from GitLab.")
        else:
            print(
                f"Failed to delete branch '{branch_name}' from GitLab: Status code {response.status_code}, "
                f"Response: {response.text}"
            )

    def _delete_merge_requests(self, project_id: str, branch_name: str) -> None:
        url = f"{self.api_url}/projects/{project_id}/merge_requests"
        response = requests.get(url, headers=self.headers, params={"source_branch": branch_name})
        if response.status_code == 200:
            merge_requests = response.json()
            for mr in merge_requests:
                if mr["source_branch"] == branch_name:
                    delete_mr_url = f"{self.api_url}/projects/{project_id}/merge_requests/{mr['iid']}"
                    del_response = requests.delete(delete_mr_url, headers=self.headers)
                    if del_response.status_code == 204:
                        print(f"Successfully deleted merge request for branch '{branch_name}'.")
                    else:
                        print(
                            f"Failed to delete merge request: Status code {del_response.status_code}, "
                            f"Response: {del_response.text}"
                        )
        else:
            print(f"Failed to fetch MRs for deletion. Status code: {response.status_code}, Response: {response.text}")
