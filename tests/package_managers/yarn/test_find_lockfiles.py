import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.package_managers.yarn.YarnPackageManager import YarnPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestYarnFindLockfiles(BasePackageManagerTest):
    @patch("splat.interface.PackageManagerInterface.is_git_ignored")
    @patch("pathlib.Path.rglob")
    def test_yarn_finds_lockfiles(self, mock_rglob: MagicMock, mock_is_git_ignored: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/project1/yarn.lock"),
            Path("/mock/path/project1/sub-dir/yarn.lock"),
        ]
        mock_is_git_ignored.return_value = False
        self._test_finds_lockfiles(YarnPackageManager, "yarn.lock", mock_rglob)

        mock_rglob.assert_called_once_with("yarn.lock")
        self.assertEqual(mock_is_git_ignored.call_count, 2)

    @patch("splat.interface.PackageManagerInterface.is_git_ignored")
    @patch("pathlib.Path.rglob")
    def test_yarn_excludes_git_ignored_lockfiles(self, mock_rglob: MagicMock, mock_is_git_ignored: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/node_modules/yarn.lock"),
            Path("/mock/path/node_modules/sub-dir/yarn.lock"),
        ]
        # the files are ignored by Git
        mock_is_git_ignored.return_value = True

        self._test_returns_empty_list(YarnPackageManager, mock_rglob)
        mock_rglob.assert_called_once_with("yarn.lock")

    @patch("pathlib.Path.rglob")
    def test_yarn_ignores_unmatched_files(self, mock_rglob: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/project1/sub-dir/yarn.locke"),
            Path("/mock/path/project2/YARN.lock"),
        ]
        self._test_returns_empty_list(YarnPackageManager, mock_rglob)
        mock_rglob.assert_called_once_with("yarn.lock")

    @patch("pathlib.Path.rglob")
    def test_yarn_returns_empty_list_when_no_files_found(self, mock_rglob: MagicMock) -> None:
        mock_rglob.return_value = []
        self._test_returns_empty_list(YarnPackageManager, mock_rglob)
        mock_rglob.assert_called_once_with("yarn.lock")


if __name__ == "__main__":
    unittest.main()
