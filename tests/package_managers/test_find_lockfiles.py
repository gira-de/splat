from pathlib import Path

from splat.model import Lockfile
from tests.mocks.mock_package_manager import MockPackageManager
from tests.package_managers.base_test import BasePackageManagerTest


class TestFindLockfiles(BasePackageManagerTest):
    def setUp(self) -> None:
        super().setUp()
        self.mock_pm = MockPackageManager(
            lockfile=None, lockfile_name="dummy.lock", config=self.mock_config, ctx=self.mock_ctx
        )
        self.mock_pipenv = MockPackageManager(
            lockfile=None, lockfile_name="Pipfile.lock", config=self.mock_config, ctx=self.mock_ctx
        )

    def test_find_lockfiles_matches_glob_and_builds_relative_paths(self) -> None:
        lockfiles = [
            Path("/mock/path/dummy.lock"),
            Path("/mock/path/sub/dir/dummy.lock"),
            Path("/mock/path/project1/Pipfile.lock"),
            Path("/mock/path/project1/sub-dir/Pipfile.lock"),
        ]
        for lockfile_path in lockfiles:
            self.mock_fs.write(str(lockfile_path), "")

        result = self.mock_pm.find_lockfiles(self.project)
        result.extend(self.mock_pipenv.find_lockfiles(self.project))
        expected = [
            Lockfile(
                path=lockfile_path,
                relative_path=Path("/") / lockfile_path.relative_to(self.project.path),
            )
            for lockfile_path in lockfiles
        ]
        self.assertEqual(len(result), len(expected))
        self.assertEqual(set(result), set(expected))

    def test_find_lockfiles_ignores_non_matching_files(self) -> None:
        unmatched_lockfiles = [
            Path("/mock/path/dummy.locke"),
            Path("/mock/path/DUMMY.lock"),
            Path("/mock/path/sub/dummy.LOCK"),
            Path("/mock/path/project1/NOT_A_Pipfile.lock"),
            Path("/mock/path/project2/Another.lock"),
        ]
        for lockfile_path in unmatched_lockfiles:
            self.mock_fs.write(str(lockfile_path), "")
        result = self.mock_pm.find_lockfiles(self.project)
        result.extend(self.mock_pipenv.find_lockfiles(self.project))
        self.assertEqual(result, [])

    def test_find_lockfiles_returns_empty_when_no_files(self) -> None:
        result = self.mock_pm.find_lockfiles(self.project)
        self.assertEqual(result, [])
