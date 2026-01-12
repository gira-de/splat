import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.package_managers.poetry.PoetryPackageManager import PoetryPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestPoetryFindLockfiles(BasePackageManagerTest):
    @patch("pathlib.Path.rglob")
    def test_poetry_finds_lockfiles(self, mock_rglob: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/project1/poetry.lock"),
            Path("/mock/path/project1/sub-dir/poetry.lock"),
        ]
        self._test_finds_lockfiles(PoetryPackageManager, "poetry.lock", mock_rglob)

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
