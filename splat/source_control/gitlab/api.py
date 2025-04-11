from typing import Dict, Optional

import requests

from splat.interface.APIClient import JSON, APIClient


class GitLabAPI(APIClient):
    def __init__(self, api_url: str, access_token: str, timeout: float = 60):
        super().__init__(timeout)
        self.api_url = api_url.rstrip("/") + "/api/v4"
        self.access_token: str = access_token
        self.session = requests.Session()
        self.headers: Dict[str, str] = {"PRIVATE-TOKEN": self.access_token}

    def _build_url(self, endpoint: str) -> str:
        """
        Construct full URL by joining base API URL and endpoint.
        """
        endpoint = endpoint.lstrip("/")  # Remove any leading slash
        return f"{self.api_url}/{endpoint}"

    def get_json(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> JSON:
        """Performs a GET request and returns JSON data."""
        url: str = self._build_url(endpoint)
        response = self.session.get(url, headers=self.headers, params=params, timeout=self.timeout)
        response.raise_for_status()
        res_json: JSON = response.json()
        return res_json

    def get_bytes(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> bytes:
        """Performs a GET request and returns binary data."""
        url: str = self._build_url(endpoint)
        response = self.session.get(url, headers=self.headers, params=params, stream=True, timeout=self.timeout)
        response.raise_for_status()
        return b"".join(response.iter_content(chunk_size=8192))

    def post_json(self, endpoint: str, data: JSON) -> JSON:
        """Performs a POST request and returns JSON data."""
        url: str = self._build_url(endpoint)
        response = self.session.post(url, headers=self.headers, json=data, timeout=self.timeout)
        response.raise_for_status()
        res_json: JSON = response.json()
        return res_json

    def put_json(self, endpoint: str, data: JSON) -> JSON:
        """Performs a PUT request and returns JSON data."""
        url: str = self._build_url(endpoint)
        response = self.session.put(url, headers=self.headers, json=data, timeout=self.timeout)
        response.raise_for_status()
        res_json: JSON = response.json()
        return res_json
