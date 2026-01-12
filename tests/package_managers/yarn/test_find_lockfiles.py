import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.package_managers.yarn.YarnPackageManager import YarnPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestYarnFindLockfiles(BasePackageManagerTest):
    @patch("pathlib.Path.rglob")
    def test_yarn_finds_lockfiles(self, mock_rglob: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/project1/yarn.lock"),
            Path("/mock/path/project1/sub-dir/yarn.lock"),
        ]
        self._test_finds_lockfiles(YarnPackageManager, "yarn.lock", mock_rglob)

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
