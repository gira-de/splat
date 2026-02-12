from __future__ import annotations

from pathlib import Path

from git.exc import GitCommandError
from git.repo import Repo

from splat.config.model import GitConfig
from splat.git.interface import DEFAULT_GIT_AUTHOR_EMAIL, DEFAULT_GIT_AUTHOR_NAME, GitClientInterface, GitCommitAuthor
from splat.interface.logger import LoggerInterface
from splat.utils.errors import GitOperationError


class GitPythonClient(GitClientInterface):
    def __init__(self, repo_path: str, logger: LoggerInterface) -> None:
        self._repo = Repo(repo_path, search_parent_directories=True)
        self.logger = logger

    @classmethod
    def clone(
        cls,
        url: str,
        to_path: Path,
        logger: LoggerInterface,
        depth: int | None = None,
        no_single_branch: bool = True,
    ) -> GitPythonClient:
        """Clone a repository and return a GitPythonClient for it."""
        try:
            logger.debug(f"Cloning repository into {to_path}")
            Repo.clone_from(url=url, to_path=to_path, depth=depth, no_single_branch=no_single_branch)
            logger.info(f"Successfully cloned repository into {to_path}")
            return cls(str(to_path), logger)
        except GitCommandError as e:
            raise GitOperationError(f"Failed to clone repository into {to_path}", e)

    @property
    def working_dir(self) -> Path:
        wd = self._repo.working_tree_dir
        if wd is None:
            raise GitOperationError("Repository working directory is not set.", RuntimeError("No working directory"))
        return Path(wd)

    def branch_exists_local(self, branch: str) -> bool:
        return branch in (head.name for head in self._repo.heads)

    def branch_exists_remote(self, branch: str) -> bool:
        """Check if branch exists on the default remote ('origin')."""
        try:
            remote = self._repo.remote()  # default: 'origin'
            return any(ref.remote_head == branch for ref in remote.refs)
        except ValueError:
            # No remotes configured
            return False
        except GitCommandError as e:
            raise GitOperationError(
                f"Failed to determine if remote branch '{branch}' exists in repository '{self.working_dir}'", e
            )

    def create_branch(self, branch: str, from_ref: str = "HEAD") -> None:
        """Create a new local branch from the given ref (default: current HEAD)."""
        try:
            self._repo.git.checkout("-b", branch, from_ref)
            self.logger.info(f"Created new branch '{branch}' from {from_ref} in repository '{self.working_dir.name}'.")
        except GitCommandError as e:
            raise GitOperationError(
                f"Failed to create new branch '{branch}' from {from_ref} in repository '{self.working_dir}'", e
            )

    def switch_branch(self, branch: str) -> None:
        """Switch to an existing local branch."""
        try:
            self._repo.git.switch(branch)
            self.logger.info(f"Switched to branch '{branch}' in repository '{self.working_dir.name}'.")
        except GitCommandError as e:
            raise GitOperationError(f"Failed to switch to branch '{branch}' in repository '{self.working_dir}'", e)

    def discard_changes(self, files_to_discard: list[str] | None = None) -> None:
        """
        Discard changes in the repo.

        If files_to_discard is provided, only those files are reset;
        otherwise the whole tree is cleaned.
        """
        self.logger.debug(f"Discarding changes in {self.working_dir}")
        try:
            if files_to_discard:
                self._repo.git.checkout("--", *files_to_discard)
                self.logger.info(
                    f"Changes in the file(s) {', '.join(files_to_discard)} "
                    f"have been discarded in {self.working_dir}."
                )
            else:
                self._repo.git.reset("--hard")
                self._repo.git.clean("-fd")
                self.logger.info(f"All changes discarded in {self.working_dir}.")
        except GitCommandError as e:
            self.logger.error(f"Failed to discard local changes in {self.working_dir}: {e}")

    def is_dirty(self, include_untracked: bool = True) -> bool:
        try:
            return self._repo.is_dirty(untracked_files=include_untracked)
        except Exception as e:
            raise GitOperationError(f"Failed to determine repository state for {self.working_dir}", e)

    def is_ignored(self, file_path: str) -> bool:
        """Return True if file is ignored by git, False if not or on error."""
        try:
            result = self._repo.git.check_ignore(file_path)
            return bool(result)
        except GitCommandError:
            # git check-ignore returns non-zero if not ignored
            return False

    def stage_files(self, files: list[str]) -> None:
        try:
            self._repo.index.add([str(file) for file in files])
        except Exception as e:
            raise GitOperationError(f"Failed to stage files {files} in repository '{self.working_dir}'", e)

    def commit_files(self, files: list[str], message: str) -> bool:
        if len(files) == 0 or message == "":
            return False
        try:
            self._repo.index.add([str(file) for file in files])
            # Prevent empty commits
            if not self._repo.is_dirty(untracked_files=False):
                self.logger.debug("No changes to commit. Skipping commit.")
                return False
            self.logger.debug(f'Committing files {", ".join(str(file) for file in files)} in {self.working_dir}')
            self._repo.index.commit(message=message)
            self.logger.info(f"Created commit in '{self.working_dir.name}': {message.split('\n', 1)[0]}")
            return True
        except Exception as e:
            raise GitOperationError(f"Failed to create commit in repository '{self.working_dir}'", e)

    def pull(self, branch: str) -> None:
        try:
            remote = self._repo.remote()  # origin by default
            remote.pull(branch, rebase=True)
            self.logger.info(f"Pulled latest changes for '{branch}' in {self.working_dir.name}.")
        except GitCommandError as e:
            raise GitOperationError(f"Failed to pull branch '{branch}' for repository '{self.working_dir}'", e)

    def push(self, branch: str, force: bool = False) -> None:
        action = "Force-pushing" if force else "Pushing"
        self.logger.debug(f"{action} changes in {self.working_dir} for branch {branch}")
        try:
            remote = self._repo.remote()  # origin by default
            push_info = remote.push(refspec=f"{branch}:{branch}", force=force)

            errors = [info.summary for info in push_info if info.flags & info.ERROR]
            if errors:
                raise GitOperationError(
                    f"Push failed for branch '{branch}' in '{self.working_dir}': " + "; ".join(errors),
                    RuntimeError("; ".join(errors)),
                )
            for info in push_info:
                self.logger.info(f"Pushed {info.local_ref} to {info.remote_ref}")
        except GitCommandError as e:
            raise GitOperationError("An error occurred while pushing changes", e)

    def configure_identity(self, git_cfg: GitConfig) -> None:
        author_name = git_cfg.author_name or DEFAULT_GIT_AUTHOR_NAME
        author_email = git_cfg.author_email or DEFAULT_GIT_AUTHOR_EMAIL

        if git_cfg.author_email and git_cfg.author_name is None:
            self.logger.debug(
                f"Git author email provided without a name for {self.working_dir}. "
                f"Using default author name '{DEFAULT_GIT_AUTHOR_NAME}'."
            )
        elif git_cfg.author_email is None:
            self.logger.debug(
                f"No git author identity provided for {self.working_dir}. "
                f"Using defaults {author_name} <{author_email}>."
            )

        try:
            with self._repo.config_writer() as config_writer:
                config_writer.set_value("user", "name", author_name)
                config_writer.set_value("user", "email", author_email)
            self.logger.info(f"Configured git author identity for {self.working_dir}: {author_name} <{author_email}>")
        except Exception as e:
            self.logger.error(f"Failed to configure git author identity for {self.working_dir}: {e}")
            raise GitOperationError("Failed to configure git author identity", e)

    def get_commit_authors_between(self, base_ref: str, branch_ref: str) -> list[GitCommitAuthor]:
        return [
            GitCommitAuthor(name=commit.author.name or "", email=commit.author.email or "")
            for commit in self._repo.iter_commits(f"{base_ref}..{branch_ref}")
        ]

    def reset_branch_to_ref(self, branch: str, base_ref: str) -> None:
        try:
            self._repo.git.reset("--hard", base_ref)
            self.logger.info(f"Branch '{branch}' reset to {base_ref} for project '{self.working_dir.name}'.")
        except GitCommandError as e:
            raise GitOperationError(
                f"Failed to reset branch '{branch}' to {base_ref} for project '{self.working_dir}'", e
            )
