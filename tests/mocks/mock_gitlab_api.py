from typing import Dict, List, cast

from splat.interface.APIClient import JSON
from splat.source_control.gitlab.api import GitLabAPI


class MockGitLabAPI(GitLabAPI):
    def __init__(
        self,
        api_url: str,
        access_token: str = "dummy",  # nosec
        timeout: float = 10.0,
        get_json_response: JSON = None,
        get_json_by_endpoint: dict[str, JSON] | None = None,
        get_json_error: Exception | None = None,
        get_bytes_response: bytes = b"",
        post_json_response: JSON = None,
        put_json_response: JSON = None,
        put_json_error: Exception | None = None,
    ) -> None:
        super().__init__(api_url, access_token, timeout=timeout)
        self._get_json_response = get_json_response
        self._get_json_by_endpoint = get_json_by_endpoint or {}
        self._get_json_error = get_json_error
        self._get_bytes_response = get_bytes_response
        self._post_json_response = post_json_response
        self._put_json_response = put_json_response
        self._put_json_error = put_json_error
        self.get_calls: list[tuple[str, Dict[str, str] | None]] = []
        self.post_calls: list[tuple[str, dict[str, JSON]]] = []
        self.put_calls: list[tuple[str, dict[str, JSON]]] = []

    def get_json(self, endpoint: str, params: Dict[str, str] | None = None) -> JSON:
        self.get_calls.append((endpoint, params))
        if self._get_json_error:
            raise self._get_json_error
        if endpoint in self._get_json_by_endpoint:
            return self._get_json_by_endpoint[endpoint]
        if params and "page" in params:  # pagination
            responses = cast(List[JSON], self._get_json_response)
            try:
                page = int(params["page"])
                return responses[page - 1]
            except IndexError:
                return []
        return self._get_json_response

    def get_bytes(self, endpoint: str, params: Dict[str, str] | None = None) -> bytes:
        return self._get_bytes_response

    def post_json(self, endpoint: str, data: JSON) -> JSON:
        if not isinstance(data, dict):
            raise TypeError("MockGitLabAPI.post_json expected dict payload")
        self.post_calls.append((endpoint, data))
        return self._post_json_response

    def put_json(self, endpoint: str, data: JSON) -> JSON:
        if not isinstance(data, dict):
            raise TypeError("MockGitLabAPI.put_json expected dict payload")
        self.put_calls.append((endpoint, data))
        if self._put_json_error:
            raise self._put_json_error
        return self._put_json_response
