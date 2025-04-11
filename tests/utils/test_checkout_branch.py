import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.utils.git_operations import checkout_branch


class TestCheckoutBranch(unittest.TestCase):
    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_checkout_branch_checks_out_existing_remote_branch(
        self, mock_logger: MagicMock, mock_repo: MagicMock
    ) -> None:
        repo_path = Path("/path/to/repo")
        branch_name = "existing-remote-branch"
        mock_git = mock_repo.return_value.git
        mock_remote = mock_repo.return_value.remote.return_value

        # Mock the return value of symbolic_ref to simulate 'HEAD' branch
        mock_git.symbolic_ref.return_value = "refs/remotes/origin/HEAD"

        # Mock the remote refs to include the branch
        mock_remote.refs = {branch_name: MagicMock()}

        checkout_branch(repo_path, branch_name, is_local_project=False)

        # Assert that the branch was checked out and pulled
        mock_git.checkout.assert_any_call(branch_name)
        mock_remote.pull.assert_called_once_with(branch_name)

        # Check the correct log message with the mocked branch name
        mock_logger.info.assert_called_with(
            f"Checked out and pulled from existing remote branch '{branch_name}' "
            f"in repository '{repo_path.name}' (default branch: 'HEAD')"
        )

    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_checkout_branch_checks_out_existing_local_branch(
        self, mock_logger: MagicMock, mock_repo: MagicMock
    ) -> None:
        repo_path = Path("/path/to/repo")
        branch_name = "existing-local-branch"
        mock_git = mock_repo.return_value.git
        mock_repo.return_value.heads = {branch_name: MagicMock()}

        mock_git.symbolic_ref.return_value = "refs/remotes/origin/HEAD"

        checkout_branch(repo_path, branch_name, is_local_project=True)

        # Assert that the branch was checked out
        mock_git.checkout.assert_called_once_with(branch_name)
        mock_logger.info.assert_called_with(
            f"Checked out existing local branch '{branch_name}' in repository '{repo_path.name}' "
            f"(default branch: 'HEAD')"
        )

    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_checkout_branch_creates_and_checks_out_new_branch(
        self, mock_logger: MagicMock, mock_repo: MagicMock
    ) -> None:
        repo_path = Path("/path/to/repo")
        branch_name = "new-branch"
        mock_git = mock_repo.return_value.git
        mock_repo.return_value.heads = {}

        mock_git.symbolic_ref.return_value = "refs/remotes/origin/HEAD"

        checkout_branch(repo_path, branch_name, is_local_project=True)

        # Assert that a new branch was created and checked out
        mock_git.checkout.assert_called_once_with("HEAD", b=branch_name)
        mock_logger.info.assert_called_with(
            f"Created and checked out new branch '{branch_name}' in repository '{repo_path.name}' "
            f"(from default branch: 'HEAD')"
        )

    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_checkout_branch_logs_error_on_failure(self, mock_logger: MagicMock, mock_repo: MagicMock) -> None:
        repo_path = Path("/path/to/repo")
        branch_name = "branch-name"
        mock_git = mock_repo.return_value.git

        mock_git.checkout.side_effect = Exception("Checkout failed")

        checkout_branch(repo_path, branch_name, is_local_project=True)

        mock_logger.error.assert_called_once_with(
            f"Failed to checkout, pull, or create branch '{branch_name}' in repository '{repo_path}': Checkout failed"
        )


if __name__ == "__main__":
    unittest.main()
