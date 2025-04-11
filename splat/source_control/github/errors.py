from typing import Literal

from requests import Response


class GithubHTTPError(Exception):
    def __init__(self, message: str, response: Response) -> None:
        message_with_response_info = message + f"{response.status_code} - {response.text}"
        super().__init__(message_with_response_info)
        self.message = message_with_response_info


class GithubPullRequestError(GithubHTTPError):
    def __init__(self, project: str, response: Response, operation: Literal["create", "fetch", "update"]) -> None:
        match operation:
            case "create":
                message = f"Failed to create pull request for {project}: "
            case "fetch":
                message = f"Failed to fetch pull requests for {project}: "
            case "update":
                message = f"Failed to update pull request for {project}: "
            case _:
                message = "HTTP Error: "
        super().__init__(message, response)
        self.operation = operation
        self.project = project
