import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
SYSTEM_TESTS_DIR = PROJECT_ROOT / "system_tests"

CLONE_DIR = Path("/splat/splat_repos")
GITLAB_PROJECT = "gira-de/splat-system-test-gitlab"
GITHUB_PROJECT = "gira-de/splat-system-test"


# GitLab and GitHub API Information
GITLAB_API_URL = "https://gitlab.com/api/v4"
GITHUB_API_URL = "https://api.github.com"
GITHUB_REPO_OWNER = "gira-de"
GITLAB_TOKEN = os.getenv("SYSTEM_TEST_GITLAB_ACCESS_TOKEN")
GITHUB_TOKEN = os.getenv("SYSTEM_TEST_GITHUB_ACCESS_TOKEN")
