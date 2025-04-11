import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.utils.git_operations import clean_up_project_dir


class TestCleanUpProjectDir(unittest.TestCase):
    @patch("splat.utils.git_operations.shutil.rmtree")
    @patch("splat.utils.git_operations.logger")
    def test_clean_up_project_dir_removes_directory_and_logs(
        self, mock_logger: MagicMock, mock_rmtree: MagicMock
    ) -> None:
        project_dir = Path("/path/to/project")

        clean_up_project_dir(project_dir)

        mock_rmtree.assert_called_once_with(project_dir)
        mock_logger.debug.assert_called_once_with(f"Removing {project_dir.name}")

    @patch("splat.utils.git_operations.shutil.rmtree")
    @patch("splat.utils.git_operations.logger")
    def test_clean_up_project_dir_logs_error_on_removal_failure(
        self, mock_logger: MagicMock, mock_rmtree: MagicMock
    ) -> None:
        project_dir = Path("/path/to/project")

        mock_rmtree.side_effect = Exception("Removal failed")

        clean_up_project_dir(project_dir)

        mock_logger.error.assert_called_once_with(
            f"Failed to remove project directory {project_dir.name}: Removal failed"
        )

    @patch("splat.utils.git_operations.shutil.rmtree")
    @patch("splat.utils.git_operations.logger")
    def test_clean_up_project_dir_handles_nonexistent_directory(
        self, mock_logger: MagicMock, mock_rmtree: MagicMock
    ) -> None:
        project_dir = Path("/path/to/nonexistent")

        mock_rmtree.side_effect = FileNotFoundError("Directory not found")

        clean_up_project_dir(project_dir)

        mock_logger.error.assert_called_once_with(
            f"Failed to remove project directory {project_dir.name}: Directory not found"
        )
