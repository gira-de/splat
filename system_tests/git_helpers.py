import subprocess
from pathlib import Path


def get_git_log(project_path: Path) -> str:
    try:
        resut = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=project_path,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        return resut.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to retrieve commit log for '{project_path}': {e.stderr}")


def verify_branch_pushed(project_path: Path, branch_name: str) -> bool:
    try:
        # Run `git ls-remote --heads origin <branch_name>` to check if the branch exists on the remote
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch_name],
            cwd=project_path,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        print(f"✔ Verified that {project_path} has branch {branch_name}", flush=True)
        return bool(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to verify branch '{branch_name}' for '{project_path}': {e.stderr}")
