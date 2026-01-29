from __future__ import annotations

from abc import ABC, abstractmethod

# Define a recursive JSON type
JSON = str | int | float | bool | None | dict[str, "JSON"] | list["JSON"]


class APIClient(ABC):
    """Abstract interface for interacting with different APIs (GitLab, GitHub, etc.)."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    @abstractmethod
    def get_json(self, endpoint: str, params: dict[str, str] | None = None) -> JSON:
        """Makes a GET request and returns JSON data."""
        pass

    @abstractmethod
    def get_bytes(self, endpoint: str, params: dict[str, str] | None = None) -> bytes:
        """Makes a GET request and returns binary data."""
        pass

    @abstractmethod
    def post_json(self, endpoint: str, data: JSON) -> JSON:
        """Makes a POST request and returns JSON data."""
        pass
