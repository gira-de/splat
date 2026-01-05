import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from splat.package_managers.pipenv.PipenvPackageManager import PipenvPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestPipenvFindLockfiles(BasePackageManagerTest):
    @patch("pathlib.Path.rglob")
    def test_pipenv_finds_lockfiles(self, mock_rglob: MagicMock) -> None:
        mock_rglob.return_value = [
            Path("/mock/path/project1/Pipfile.lock"),
            Path("/mock/path/project1/sub-dir/Pipfile.lock"),
        ]
        self._test_finds_lockfiles(PipenvPackageManager, "Pipfile.lock", mock_rglob)

        mock_rglob.assert_called_once_with("Pipfile.lock")

    @patch("pathlib.Path.rglob")
    def test_pipenv_ignores_unmatched_files(self, mock_rglob: MagicMock) -> None:
        unmatched_lockfiles = [
            Path("/mock/path/project1/NOT_A_Pipfile.lock"),
            Path("/mock/path/project2/Another.lock"),
        ]
        mock_rglob.return_value = [unmatched_lockfiles]
        self._test_returns_empty_list(PipenvPackageManager, mock_rglob)

        mock_rglob.assert_called_once_with("Pipfile.lock")

    @patch("pathlib.Path.rglob")
    def test_pipenv_returns_empty_list_when_no_files_found(
        self,
        mock_rglob: MagicMock,
    ) -> None:
        mock_rglob.return_value = []
        self._test_returns_empty_list(PipenvPackageManager, mock_rglob)

        mock_rglob.assert_called_once_with("Pipfile.lock")


if __name__ == "__main__":
    unittest.main()
