import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.package_managers.uv.UvPackageManager import UvPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestUvFindLockfiles(BasePackageManagerTest):
    @patch("pathlib.Path.rglob")
    def test_uv_finds_lockfiles(self, mock_rglob: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/project1/uv.lock"),
            Path("/mock/path/project1/sub-dir/uv.lock"),
        ]
        self._test_finds_lockfiles(UvPackageManager, "uv.lock", mock_rglob)

        mock_rglob.assert_called_once_with("uv.lock")

    @patch("pathlib.Path.rglob")
    def test_uv_ignores_unmatched_files(self, mock_rglob: MagicMock) -> None:
        unmatched_lockfiles = [
            Path("project1/POETRY.lock"),
            Path("project2/Auv.lock"),
        ]
        mock_rglob.return_value = [unmatched_lockfiles]

        self._test_returns_empty_list(UvPackageManager, mock_rglob)

    @patch("pathlib.Path.rglob")
    def test_uv_returns_and_empty_list_when_base_path_is_empty(self, mock_rglob: MagicMock) -> None:
        mock_rglob.return_value = []
        self._test_returns_empty_list(UvPackageManager, mock_rglob)
        mock_rglob.assert_called_once_with("uv.lock")


if __name__ == "__main__":
    unittest.main()
