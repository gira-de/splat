import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.package_managers.poetry.PoetryPackageManager import PoetryPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestPoetryFindLockfiles(BasePackageManagerTest):
    @patch("splat.interface.PackageManagerInterface.is_git_ignored")
    @patch("pathlib.Path.rglob")
    def test_poetry_finds_lockfiles(self, mock_rglob: MagicMock, mock_is_git_ignored: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/project1/poetry.lock"),
            Path("/mock/path/project1/sub-dir/poetry.lock"),
        ]
        mock_is_git_ignored.return_value = False
        self._test_finds_lockfiles(PoetryPackageManager, "poetry.lock", mock_rglob)

        mock_rglob.assert_called_once_with("poetry.lock")
        self.assertEqual(mock_is_git_ignored.call_count, 2)

    @patch("splat.interface.PackageManagerInterface.is_git_ignored")
    @patch("pathlib.Path.rglob")
    def test_yarn_excludes_git_ignored_lockfiles(self, mock_rglob: MagicMock, mock_is_git_ignored: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/.venv/poetry.lock"),
            Path("/mock/path/.venv/sub-bin/poetry.lock"),
        ]
        # the files are ignored by Git
        mock_is_git_ignored.return_value = True

        self._test_returns_empty_list(PoetryPackageManager, mock_rglob)
        mock_rglob.assert_called_once_with("poetry.lock")

    @patch("pathlib.Path.rglob")
    def test_poetry_ignores_unmatched_files(self, mock_rglob: MagicMock) -> None:
        unmatched_lockfiles = [
            Path("project1/POETRY.lock"),
            Path("project2/Apoetry.lock"),
        ]
        mock_rglob.return_value = [unmatched_lockfiles]

        self._test_returns_empty_list(PoetryPackageManager, mock_rglob)

    @patch("pathlib.Path.rglob")
    def test_poetry_returns_and_empty_list_when_base_path_is_empty(self, mock_rglob: MagicMock) -> None:
        mock_rglob.return_value = []
        self._test_returns_empty_list(PoetryPackageManager, mock_rglob)
        mock_rglob.assert_called_once_with("poetry.lock")


if __name__ == "__main__":
    unittest.main()
