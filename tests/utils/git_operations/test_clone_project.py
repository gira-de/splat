import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from splat.model import RemoteProject
from splat.utils.git_operations import clone_project


class TestCloneProjects(unittest.TestCase):
    @patch("splat.utils.git_operations.Repo.clone_from")
    @patch("splat.utils.git_operations.shutil.rmtree")
    @patch("splat.utils.git_operations.Path.exists", return_value=False)
    @patch("splat.utils.git_operations.logger")
    def test_calls_the_repo_clone_from_class_method_for_project_and_logs_progress(
        self,
        mock_logger: MagicMock,
        _: MagicMock,
        mock_rmtree: MagicMock,
        mock_clone_from: MagicMock,
    ) -> None:
        projects_to_clone = RemoteProject(
            id=1,
            name_with_namespace="group/project1",
            clone_url="https://git.example.com/project1.git",
            web_url="https://git.example.com/project1",
            default_branch="main",
        )
        base_path = "/mock/base/path"
        access_token = "mock_access_token"  # nosec

        clone_project(projects_to_clone, base_path, access_token)

        expected_clone_url = f"https://oauth2:{access_token}@git.example.com/project1.git"
        expected_clone_path = Path(base_path) / "group-project1"
        mock_clone_from.assert_called_once_with(
            url=expected_clone_url, to_path=expected_clone_path, no_single_branch=True
        )

        expected_log_calls = [
            call.debug(f"Cloning group/project1 into {expected_clone_path}"),
            call.info(f"Successfully cloned group/project1 into {expected_clone_path}"),
        ]
        mock_logger.assert_has_calls(expected_log_calls)

    @patch("splat.utils.git_operations.Repo.clone_from")
    @patch("splat.utils.git_operations.shutil.rmtree")
    @patch("splat.utils.git_operations.Path.exists", return_value=True)
    @patch("splat.utils.git_operations.logger")
    def test_clone_project_overwrites_existing_project(
        self,
        mock_logger: MagicMock,
        _: MagicMock,
        mock_rmtree: MagicMock,
        mock_clone_from: MagicMock,
    ) -> None:
        project_to_clone = RemoteProject(
            id=1,
            name_with_namespace="group/project1",
            clone_url="https://git.example.com/project1.git",
            web_url="https://git.example.com/project1",
            default_branch="main",
        )

        base_path = "/mock/base/path"
        access_token = "mock_access_token"  # nosec

        clone_project(project_to_clone, base_path, access_token)

        expected_clone_path = Path(base_path) / "group-project1"
        mock_rmtree.assert_called_once_with(expected_clone_path)

        expected_clone_url = f"https://oauth2:{access_token}@git.example.com/project1.git"
        mock_clone_from.assert_called_once_with(
            url=expected_clone_url, to_path=expected_clone_path, no_single_branch=True
        )

        expected_log_calls = [
            call.debug(f"Directory {expected_clone_path} already exists. Removing it.."),
            call.debug(f"Cloning group/project1 into {expected_clone_path}"),
            call.info(f"Successfully cloned group/project1 into {expected_clone_path}"),
        ]
        mock_logger.assert_has_calls(expected_log_calls)


if __name__ == "__main__":
    unittest.main()
