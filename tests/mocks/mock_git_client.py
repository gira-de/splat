from pathlib import Path

from splat.git.interface import GitClientInterface


class MockGitClient(GitClientInterface):
    def __init__(self, repo_path: Path) -> None:
        self._working_dir = repo_path
        self.local_branches: set[str] = set()
        self.remote_branches: set[str] = set()
        self.current_branch: str | None = None
        self.commit_calls: list[tuple[list[str], str]] = []
        self.push_calls: list[str] = []
        self.discard_calls: list[list[str] | None] = []

    @property
    def working_dir(self) -> Path:
        return self._working_dir

    def branch_exists_local(self, branch_name: str) -> bool:
        return branch_name in self.local_branches

    def branch_exists_remote(self, branch_name: str) -> bool:
        return branch_name in self.remote_branches

    def create_branch(self, branch_name: str, from_ref: str = "HEAD") -> None:
        self.local_branches.add(branch_name)
        self.current_branch = branch_name

    def switch_branch(self, branch_name: str) -> None:
        self.current_branch = branch_name

    def discard_changes(self, files_to_discard: list[str] | None = None) -> None:
        self.discard_calls.append(files_to_discard)

    def is_dirty(self, include_untracked: bool = True) -> bool:
        return False

    def is_ignored(self, file_path: str) -> bool:
        return False

    def commit_files(self, files: list[str], message: str) -> bool:
        self.commit_calls.append((list(files), message))
        return True

    def pull(self, branch_name: str) -> None:
        return None

    def push(self, branch_name: str) -> None:
        self.push_calls.append(branch_name)
