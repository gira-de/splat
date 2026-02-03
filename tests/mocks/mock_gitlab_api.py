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
        get_bytes_response: bytes = b"",
        post_json_response: JSON = None,
        put_json_response: JSON = None,
    ) -> None:
        super().__init__(api_url, access_token, timeout=timeout)
        self._get_json_response = get_json_response
        self._get_bytes_response = get_bytes_response
        self._post_json_response = post_json_response
        self._put_json_response = put_json_response

    def get_json(self, endpoint: str, params: Dict[str, str] | None = None) -> JSON:
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
        return self._post_json_response

    def put_json(self, endpoint: str, data: JSON) -> JSON:
        return self._put_json_response
