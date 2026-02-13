import os
import time
import unittest
from pathlib import Path

from system_tests import GITHUB_PROJECT, GITHUB_REPO_OWNER, GITLAB_PROJECT, SYSTEM_TESTS_DIR
from system_tests.api.github import GitHubAPI
from system_tests.api.gitlab import GitLabAPI
from system_tests.git_helpers import get_remote_head_sha, verify_branch_pushed
from system_tests.test_utils import (
    cleanup_projects,
    run_splat,
    update_config_with_branch,
    verify_project_cloned,
)

ABORT_BRANCH_NAME = "splat-abort-branch-fixture"
RESET_BRANCH_NAME = "splat-reset-branch"


class TestBranchRegression(unittest.TestCase):
    def setUp(self) -> None:
        self.config_file = SYSTEM_TESTS_DIR / "splat.yaml"
        self.original_config_content = self.config_file.read_text()
        self.original_mock_audit_env = os.environ.get("MOCK_AUDIT")
        os.environ["MOCK_AUDIT"] = "true"

        self.gitlab_api = GitLabAPI()
        self.github_api = GitHubAPI()
        self.branch_name: str | None = None

    def tearDown(self) -> None:
        self.config_file.write_text(self.original_config_content)
        os.environ.pop("MOCK_AUDIT", None)
        cleanup_projects([GITLAB_PROJECT, GITHUB_PROJECT])

    def _cleanup_remote_branch(self, branch_name: str) -> None:
        self.gitlab_api.cleanup_branch_and_merge_request(GITLAB_PROJECT, branch_name)
        self.github_api.cleanup_branch_and_pull_request(GITHUB_PROJECT, GITHUB_REPO_OWNER, branch_name)

    def _assert_branch_exists_on_both_platforms(self, gitlab_project_path: Path, github_project_path: Path) -> None:
        self.assertTrue(
            verify_branch_pushed(gitlab_project_path, self.branch_name or ""),
            f"Branch '{self.branch_name}' not found in remote for GitLab project '{GITLAB_PROJECT}'.",
        )
        self.assertTrue(
            verify_branch_pushed(github_project_path, self.branch_name or ""),
            f"Branch '{self.branch_name}' not found in remote for GitHub project '{GITHUB_PROJECT}'.",
        )

    def test_splat_resets_and_reprocesses_existing_splat_branch_with_force_push(self) -> None:
        self.branch_name = RESET_BRANCH_NAME
        self.addCleanup(self._cleanup_remote_branch, self.branch_name)
        update_config_with_branch(
            self.config_file,
            self.branch_name,
            package_managers={
                "yarn": {"enabled": True},
                "pipenv": {"enabled": False},
                "poetry": {"enabled": False},
                "uv": {"enabled": False},
            },
        )
        run_splat(SYSTEM_TESTS_DIR)

        gitlab_project_path = verify_project_cloned(GITLAB_PROJECT)
        github_project_path = verify_project_cloned(GITHUB_PROJECT)
        self._assert_branch_exists_on_both_platforms(gitlab_project_path, github_project_path)

        gitlab_before_sha = get_remote_head_sha(gitlab_project_path, self.branch_name)
        github_before_sha = get_remote_head_sha(github_project_path, self.branch_name)

        time.sleep(2)
        run_splat(SYSTEM_TESTS_DIR)

        gitlab_after_sha = get_remote_head_sha(gitlab_project_path, self.branch_name)
        github_after_sha = get_remote_head_sha(github_project_path, self.branch_name)

        self.assertNotEqual(gitlab_before_sha, gitlab_after_sha, "Expected GitLab branch head SHA to be rewritten.")
        self.assertNotEqual(github_before_sha, github_after_sha, "Expected GitHub branch head SHA to be rewritten.")

        gitlab_mr = self.gitlab_api.fetch_merge_request_for_branch(GITLAB_PROJECT, self.branch_name)
        self.assertEqual(gitlab_mr["source_branch"], self.branch_name)

        github_pr = self.github_api.fetch_pull_request_for_branch(GITHUB_PROJECT, GITHUB_REPO_OWNER, self.branch_name)
        self.assertEqual(github_pr["head"]["ref"], self.branch_name)

    def test_splat_aborts_processing_project_when_manual_changes_found(self) -> None:
        self.branch_name = ABORT_BRANCH_NAME
        update_config_with_branch(
            self.config_file,
            self.branch_name,
            package_managers={
                "yarn": {"enabled": True},
                "pipenv": {"enabled": False},
                "poetry": {"enabled": False},
                "uv": {"enabled": False},
            },
        )

        logs = run_splat(SYSTEM_TESTS_DIR)

        self.assertIn(
            f"Aborted processing project: '{GITLAB_PROJECT}' to avoid overwriting manual work.",
            logs,
        )
        self.assertIn(
            f"Aborted processing project: '{GITHUB_PROJECT}' to avoid overwriting manual work.",
            logs,
        )
        self.assertIn(f"Sending project processing aborted notification for: {GITLAB_PROJECT}", logs)
        self.assertIn(f"Sending project processing aborted notification for: {GITHUB_PROJECT}", logs)


if __name__ == "__main__":
    unittest.main()
