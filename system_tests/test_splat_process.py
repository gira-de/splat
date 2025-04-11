import os
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

import yaml

from system_tests import (
    CLONE_DIR,
    GITHUB_PROJECT,
    GITHUB_REPO_OWNER,
    GITLAB_PROJECT,
    SYSTEM_TESTS_DIR,
)
from system_tests.api.github import GitHubAPI
from system_tests.api.gitlab import GitLabAPI
from system_tests.git_helpers import get_git_log, verify_branch_pushed


def log_success(message: str) -> None:
    print(f"✔ {message}", flush=True)


def update_config_with_unique_branch(config_file: Path) -> str:
    # Generate a unique branch name
    unique_branch_name = f"splat-{uuid.uuid4().hex[:8]}"
    # Read and update the config file with the unique branch name
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    config["general"]["git"]["branch_name"] = unique_branch_name
    with open(config_file, "w") as f:
        yaml.safe_dump(config, f)
    return unique_branch_name


class TestSplatProcess(unittest.TestCase):
    def cleanup_projects(self, pl: list[str]) -> None:
        for project in pl:
            try:
                project_path = CLONE_DIR / project.replace("/", "-")
                shutil.rmtree(project_path)
            except Exception as e:
                self.fail(f"Failed to remove project directory {project}: {e}")

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["MOCK_AUDIT"] = "true"
        cls.gitlab_api = GitLabAPI()
        cls.github_api = GitHubAPI()
        config_file = SYSTEM_TESTS_DIR / "splat.yaml"
        cls.unique_branch_name = update_config_with_unique_branch(config_file)

    @classmethod
    def tearDownClass(cls) -> None:
        del os.environ["MOCK_AUDIT"]
        cls.gitlab_api.cleanup_branch_and_merge_request(GITLAB_PROJECT, cls.unique_branch_name)
        cls.github_api.cleanup_branch_and_pull_request(GITHUB_PROJECT, GITHUB_REPO_OWNER, cls.unique_branch_name)
        cls().cleanup_projects([GITLAB_PROJECT, GITHUB_PROJECT])

    def run_splat(self) -> str:
        try:
            log_success("Executing splat...")
            res = subprocess.run(
                ["splat"],
                cwd=SYSTEM_TESTS_DIR,
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return res.stdout + res.stderr
        except subprocess.CalledProcessError as e:
            self.fail(f"system test failed: splat command failed with error: {e.stderr}")

    def verify_project_cloned(self, project_name: str) -> Path:
        project_path = CLONE_DIR / project_name.replace("/", "-")
        self.assertTrue(
            project_path.exists() and project_path.is_dir(),
            f"Expected cloned project directory '{project_path}' does not exist.",
        )
        log_success(f"Verified that project {project_name} has been cloned")
        return project_path

    def assert_in_no_log(self, expected, actual, message=None):
        """Custom assertIn to suppress log dumping in failure"""
        if expected not in actual:
            msg = f"{message or ''} Expected '{expected}' not found."
            raise AssertionError(msg)

    def test_splat_process_remote_projects(self) -> None:
        logs = self.run_splat()

        try:
            gitlab_project_path = self.verify_project_cloned(GITLAB_PROJECT)
            github_project_path = self.verify_project_cloned(GITHUB_PROJECT)

            expected_commit_messages = [
                "fix: Security: Update requests from 2.31.0 to 2.32.0 in /pipenv-project/Pipfile.lock",
                "fix: Security: Update flask from 0.12 to 2.2.5 in /pipenv-project/Pipfile.lock",
                "fix: Security: Update requests from 2.31.0 to 2.32.0 in /poetry-project/poetry.lock",
                "fix: Security: Update pyjwt from 1.5.0 to 2.4.0 in /poetry-project/poetry.lock",
                "fix: Security: Update flask from 0.12 to 2.2.5 in /poetry-project/poetry.lock",
                "fix: Security [high 🔴]: Update rollup from 2.77.3 to 2.79.2 in /yarn-project/yarn.lock",
                "fix: Security [moderate 🟠]: Update vite from 2.9.18 to 3.2.11 in /yarn-project/yarn.lock",
                "fix: Security [moderate 🟠]: Update svelte from 3.59.2 to 4.2.19 in /yarn-project/yarn.lock",
                "fix: Security: Update requests from 2.31.0 to 2.32.0 in /uv-project/uv.lock",
                "fix: Security: Update pyjwt from 1.5.0 to 2.4.0 in /uv-project/uv.lock",
                "fix: Security: Update flask from 0.12 to 2.2.5 in /uv-project/uv.lock",
            ]

            gitlab_git_log = get_git_log(gitlab_project_path)
            github_git_log = get_git_log(github_project_path)

            for expected_msg in expected_commit_messages:
                self.assertIn(
                    expected_msg,
                    gitlab_git_log,
                    f"Expected commit message '{expected_msg}' not found in the repository at '{gitlab_project_path}'.",
                )
                self.assertIn(
                    expected_msg,
                    github_git_log,
                    f"Expected commit message '{expected_msg}' not found in the repository at '{github_project_path}'.",
                )
            log_success("Verified commit messages for gitlab and github")

            is_branch_pushed_gitlab = verify_branch_pushed(gitlab_project_path, self.unique_branch_name)
            is_branch_pushed_github = verify_branch_pushed(github_project_path, self.unique_branch_name)
            self.assertTrue(
                is_branch_pushed_gitlab,
                f"Branch '{self.unique_branch_name}' not found in remote for GitLab project {GITLAB_PROJECT}",
            )
            self.assertTrue(
                is_branch_pushed_github,
                f"Branch '{self.unique_branch_name}' not found in remote for GitHub project {GITHUB_PROJECT}",
            )

            expected_mr_title = "Splat Dependency Updates"
            merge_request = self.gitlab_api.fetch_merge_request_for_branch(GITLAB_PROJECT, self.unique_branch_name)
            self.assertEqual(
                merge_request["title"],
                expected_mr_title,
                f"Merge Request title does not match for project '{GITLAB_PROJECT}'",
            )
            log_success("Verified gitlab merge request")
            for commit_msg in expected_commit_messages:
                self.assertIn(
                    commit_msg,
                    merge_request["description"],
                    f"Merge Request description does not match for project '{GITLAB_PROJECT}'.",
                )
            log_success("Verified gitlab merge request description")

            pull_request = self.github_api.fetch_pull_request_for_branch(
                GITHUB_PROJECT, GITHUB_REPO_OWNER, self.unique_branch_name
            )
            self.assertEqual(
                pull_request["title"],
                expected_mr_title,
                f"Pull Request title does not match for repository {GITHUB_PROJECT}'."
                f"Expected: '{expected_mr_title}'.",
            )
            log_success("Verified github pull request")
            for commit_msg in expected_commit_messages:
                self.assertIn(
                    commit_msg,
                    pull_request["body"],
                    f"Pull Request description does not match for repository '{GITHUB_PROJECT}'.",
                )
            log_success("Verified github pull request description")

            expected_notification_logs = [
                f"Sending notification: Merge Request Created on GitLab for: {GITLAB_PROJECT}",
                "Notification sent successfully",
                f"Sending notification: Pull Request Created on Github for: {GITHUB_PROJECT}",
                "Notification sent successfully",
            ]
            for expected_log in expected_notification_logs:
                self.assert_in_no_log(
                    expected_log,
                    logs,
                    f"Expected notification log {expected_log} not found in the logs.",
                )
            log_success("Verified notification log messages")
            log_success("System tests succeeded")

        except AssertionError as e:
            # Print logs only if the test fails
            print("Test failed. Printing logs:", flush=True)
            print(logs, flush=True)
            raise e  # Re-raise the exception to fail the test
