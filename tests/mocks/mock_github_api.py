from splat.interface.APIClient import JSON
from splat.source_control.github.api import GitHubAPI


class MockGitHubAPI(GitHubAPI):
    def __init__(
        self,
        domain: str = "https://github.com",
        access_token: str = "dummy",  # nosec
        timeout: float = 10.0,
    ) -> None:
        super().__init__(domain, access_token, timeout=timeout)
        self._get_request_responses: list[JSON] | None = None
        self._get_request_response: JSON | None = None
        self._get_request_error: Exception | None = None
        self._post_request_response: JSON | None = None
        self._patch_request_response: JSON | None = None
        self._post_request_error: Exception | None = None
        self._patch_request_error: Exception | None = None
        self._get_request_index = 0

    def get_json(self, endpoint: str, params: dict[str, str] | None = None) -> JSON:
        if self._get_request_error:
            raise self._get_request_error
        if self._get_request_responses is not None:
            if self._get_request_index >= len(self._get_request_responses):
                return []
            response = self._get_request_responses[self._get_request_index]
            self._get_request_index += 1
            return response
        return self._get_request_response if self._get_request_response is not None else []

    def post_json(self, endpoint: str, data: JSON) -> JSON:
        if self._post_request_error:
            raise self._post_request_error
        if self._post_request_response is None:
            return {}
        return self._post_request_response

    def patch_request(self, endpoint: str, data: JSON) -> JSON:
        if self._patch_request_error:
            raise self._patch_request_error
        if self._patch_request_response is None:
            return {}
        return self._patch_request_response
