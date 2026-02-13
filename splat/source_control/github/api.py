import requests

from splat.interface.APIClient import JSON, APIClient
from splat.interface.logger import LoggerInterface


class GitHubAPI(APIClient):
    def __init__(self, domain: str, access_token: str, logger: LoggerInterface, timeout: float = 60):
        super().__init__(timeout)
        self.api_base_url = "https://api.github.com" if domain == "https://github.com" else f"{domain}/api/v3"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.logger = logger
        self.session = requests.Session()

    def get_json(self, endpoint: str, params: dict[str, str] | None = None) -> JSON:
        url = f"{self.api_base_url}{endpoint}"
        response = self.session.get(url, headers=self.headers, params=params, timeout=self.timeout)
        response.raise_for_status()
        res_json: JSON = response.json()
        return res_json

    def get_bytes(self, endpoint: str, params: dict[str, str] | None = None) -> bytes:
        url = f"{self.api_base_url}{endpoint}"
        response = self.session.get(url, headers=self.headers, params=params, stream=True, timeout=self.timeout)
        response.raise_for_status()
        return b"".join(response.iter_content(chunk_size=8192))

    def post_json(self, endpoint: str, data: JSON) -> JSON:
        url = f"{self.api_base_url}{endpoint}"
        response = self.session.post(url, json=data, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        res_json: JSON = response.json()
        return res_json

    def patch_request(self, endpoint: str, data: JSON) -> JSON:
        url = endpoint if endpoint.startswith("http") else f"{self.api_base_url}{endpoint}"
        response = self.session.patch(url, json=data, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        res_json: JSON = response.json()
        return res_json
