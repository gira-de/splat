from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class GitClientInterface(ABC):
    @property
    @abstractmethod
    def working_dir(self) -> Path:
        pass

    @abstractmethod
    def branch_exists_local(self, branch: str) -> bool:
        pass

    @abstractmethod
    def branch_exists_remote(self, branch: str) -> bool:
        pass

    @abstractmethod
    def create_branch(self, branch: str, from_ref: str = "HEAD") -> None:
        pass

    @abstractmethod
    def switch_branch(self, branch: str) -> None:
        pass

    @abstractmethod
    def discard_changes(self, files_to_discard: list[str] | None = None) -> None:
        pass

    @abstractmethod
    def is_dirty(self, include_untracked: bool = True) -> bool:
        pass

    @abstractmethod
    def is_ignored(self, file_path: str) -> bool:
        pass

    @abstractmethod
    def commit_files(self, files: list[str], message: str) -> bool:
        """Stage given files and create a commit; returns True if a commit was created."""
        pass

    @abstractmethod
    def pull(self, branch: str) -> None:
        pass

    @abstractmethod
    def push(self, branch: str) -> None:
        pass
