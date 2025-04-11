from typing import Any, Optional

import requests

from splat.utils.logger_config import ContextLoggerAdapter
from splat.utils.logger_config import logger as github_api_logger


class GitHubAPI:
    def __init__(
        self, domain: str, access_token: str, timeout: float = 60, logger: ContextLoggerAdapter = github_api_logger
    ):
        self.api_base_url = "https://api.github.com" if domain == "https://github.com" else f"{domain}/api/v3"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.timeout = timeout
        self.logger = logger

    def get_request(self, endpoint: str, params: Optional[dict[str, str]] = None) -> str:
        url = f"{self.api_base_url}{endpoint}"
        return self._make_request("GET", url, params=params)

    def post_request(self, endpoint: str, payload: dict[str, Any]) -> str:
        url = f"{self.api_base_url}{endpoint}"
        return self._make_request("POST", url, payload=payload)

    def patch_request(self, url: str, payload: dict[str, Any]) -> str:
        return self._make_request("PATCH", url, payload=payload)

    def _make_request(
        self, method: str, url: str, params: Optional[dict[str, str]] = None, payload: Optional[dict[str, str]] = None
    ) -> str:
        try:
            response = requests.request(
                method, url, headers=self.headers, params=params, json=payload, timeout=self.timeout
            )

            if response.status_code in (200, 201):
                return response.text
            elif response.status_code == 401:
                raise ValueError("Authentication failed. Please check your GitHub credentials.")
            elif response.status_code == 404:
                raise ValueError(f"Resource not found: {url}")
            else:
                raise RuntimeError(f"Failed to fetch resource: {response.status_code} - {response.text}")

        except requests.RequestException as e:
            raise RuntimeError(f"An error occurred during the HTTP request: {e}")
