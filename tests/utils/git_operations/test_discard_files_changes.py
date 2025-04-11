import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.utils.git_operations import discard_files_changes


class TestDiscardFilesChanges(unittest.TestCase):
    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_discard_files_changes_resets_and_cleans_all_files(
        self, mock_logger: MagicMock, mock_repo: MagicMock
    ) -> None:
        repo_path = Path("/path/to/repo")
        mock_git = mock_repo.return_value.git

        # Call the function without specifying files to discard
        discard_files_changes(repo_path)

        # Assert that the reset and clean commands were called
        mock_git.reset.assert_called_once_with("--hard")
        mock_git.clean.assert_called_once_with("-fd")
        mock_logger.debug.assert_any_call("All changes in other files have been discarded.")

    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_discard_files_changes_discards_specific_files_and_logs(
        self, mock_logger: MagicMock, mock_repo: MagicMock
    ) -> None:
        repo_path = Path("/path/to/repo")
        files_to_discard = ["file1.txt", "file2.txt"]
        mock_git = mock_repo.return_value.git

        # Call the function with specific files to discard
        discard_files_changes(repo_path, files_to_discard)

        # Assert that the checkout command was called with the specific files
        mock_git.checkout.assert_called_once_with("--", *files_to_discard)
        mock_logger.info.assert_called_once_with("Changes in the file(s) file1.txt, file2.txt have been discarded.")

    @patch("splat.utils.git_operations.Repo")
    @patch("splat.utils.git_operations.logger")
    def test_discard_files_changes_logs_error_on_failure(self, mock_logger: MagicMock, mock_repo: MagicMock) -> None:
        repo_path = Path("/path/to/repo")
        files_to_discard = ["file1.txt"]
        mock_git = mock_repo.return_value.git

        # Simulate an exception being raised during the discard operation
        mock_git.checkout.side_effect = Exception("Discarding failed")

        # Call the function and expect it to handle the exception
        discard_files_changes(repo_path, files_to_discard)

        # Assert that the error was logged
        mock_logger.error.assert_called_once_with("Failed to discard local changes: Discarding failed")


if __name__ == "__main__":
    unittest.main()
