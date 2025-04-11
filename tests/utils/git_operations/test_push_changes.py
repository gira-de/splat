import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.utils.git_operations import push_changes


class TestPushChanges(unittest.TestCase):
    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_push_changes_pushes_to_remote_branch_and_logs(self, mock_logger: MagicMock, mock_repo: MagicMock) -> None:
        repo_path = Path("/path/to/repo")
        branch_name = "main"
        remote_name = "origin"

        mock_remote = mock_repo.return_value.remote.return_value
        mock_push_info = MagicMock()

        # Ensure the ERROR flag is not set
        mock_push_info.flags = 0  # No error
        mock_push_info.ERROR = 0  # No error
        mock_push_info.local_ref = branch_name
        mock_push_info.remote_ref = f"{remote_name}/{branch_name}"

        mock_remote.push.return_value = [mock_push_info]

        # Call the function to push changes
        push_changes(repo_path, branch_name, remote_name)

        # Assert that the push was called correctly
        mock_remote.push.assert_called_once_with(refspec=f"{branch_name}:{branch_name}")

        # Check the correct log message
        mock_logger.debug.assert_called_once_with(f"Pushed {branch_name} to {mock_push_info.remote_ref}")

    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_push_changes_logs_error_on_push_failure(self, mock_logger: MagicMock, mock_repo: MagicMock) -> None:
        repo_path = Path("/path/to/repo")
        branch_name = "main"
        remote_name = "origin"

        mock_remote = mock_repo.return_value.remote.return_value
        mock_push_info = MagicMock()
        mock_push_info.flags = mock_push_info.ERROR  # Simulate error
        mock_push_info.summary = "Some push error"
        mock_remote.push.return_value = [mock_push_info]

        # Call the function to push changes
        push_changes(repo_path, branch_name, remote_name)

        # Assert that the error was logged
        mock_logger.error.assert_called_once_with("Push failed: Some push error")

    @patch("splat.utils.git_operations.Repo")
    def test_push_changes_handles_nonexistent_remote(self, mock_repo: MagicMock) -> None:
        repo_path = Path("/path/to/repo")
        branch_name = "main"
        remote_name = "nonexistent_remote"

        mock_repo.return_value.remote.side_effect = ValueError("Remote not found")

        with self.assertRaises(ValueError):
            push_changes(repo_path, branch_name, remote_name)


if __name__ == "__main__":
    unittest.main()
