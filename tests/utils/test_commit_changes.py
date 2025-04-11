import unittest
from pathlib import Path
from unittest.mock import MagicMock

from splat.model import AuditReport, Dependency, DependencyType, Lockfile, VulnerabilityDetail
from splat.utils.git_operations import commit_changes


class TestCommitChanges(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = MagicMock()
        self.files_to_commit = [
            "/path/to/repo/file1.txt",
            "/path/to/repo/file2.txt",
        ]
        self.audit_report = AuditReport(
            dep=Dependency(name="package1", version="2.0.0", type=DependencyType.DIRECT),
            fixed_version="2.0.0",
            lockfile=Lockfile(path=Path("path/to/lockfile"), relative_path=Path("lockfile")),
            vuln_details=[
                VulnerabilityDetail(
                    id="XXXX-abcd-1234-eeeE",
                    description="Some vulnerability description here",
                    recommendation=["Upgrade to version 2.0.0 or later"],
                    aliases=["CVE-123-456"],
                )
            ],
        )

    def test_commit_changes_stages_and_commits_specified_files(self) -> None:
        self.repo.index.diff.return_value = ["file1"]

        # Call the function to commit changes
        commit_message = commit_changes(self.repo, self.files_to_commit, self.audit_report)

        # Assert that the files were staged and committed
        self.repo.index.add.assert_called_once_with([str(file) for file in self.files_to_commit])
        # Assert that commit was made
        self.repo.index.commit.assert_called_once()
        # Assert that a commit message was returned
        self.assertNotEqual(commit_message, "")

    def test_commit_changes_raises_error_if_no_files_to_commit(self) -> None:
        # Call the function and expect it to log an error
        with self.assertRaises(ValueError):
            commit_changes(self.repo, [], self.audit_report)

    def test_commit_changes_raises_error_on_commit_failure(self) -> None:
        # Simulate an exception being raised during the commit
        self.repo.index.diff.return_value = ["file1"]
        self.repo.index.commit.side_effect = Exception("Commit failed")

        # Call the function and expect it to handle the exception
        with self.assertRaises(Exception):
            commit_changes(self.repo, self.files_to_commit, self.audit_report)


if __name__ == "__main__":
    unittest.main()
