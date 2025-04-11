class GitlabProjectHandlerError(Exception):
    """Base exception for GitLab project handler errors."""


class GitlabProjectFetchError(GitlabProjectHandlerError):
    """Exception raised when fetching projects fails."""


class MergeRequestHandlerError(Exception):
    """Base exception for merge request handling errors."""


class MergeRequestValidationError(MergeRequestHandlerError):
    """Exception raised when merge request validation fails."""


class MergeRequestUpdateError(MergeRequestHandlerError):
    """Exception raised when updating a merge request fails."""


class MergeRequestCreationError(MergeRequestHandlerError):
    """Exception raised when creating a merge request fails."""
