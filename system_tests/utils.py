import shutil
import subprocess
import uuid
from pathlib import Path

import yaml

from system_tests import CLONE_DIR, SYSTEM_TESTS_DIR


def log_success(message: str) -> None:
    print(f"✔ {message}", flush=True)


def update_config_with_branch(
    config_file: Path,
    branch_name: str,
    package_managers: dict[str, dict[str, bool]] | None = None,
) -> None:
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)
    config["general"]["git"]["branch_name"] = branch_name
    if package_managers is not None:
        config["package_managers"] = package_managers
    with open(config_file, "w") as file:
        yaml.safe_dump(config, file)


def update_config_with_unique_branch(config_file: Path, prefix: str = "splat") -> str:
    unique_branch_name = f"{prefix}-{uuid.uuid4().hex[:8]}"
    update_config_with_branch(config_file, unique_branch_name)
    return unique_branch_name


def run_splat(cwd: Path = SYSTEM_TESTS_DIR) -> str:
    config_file = cwd / "splat.yaml"
    if not config_file.exists():
        raise RuntimeError(f"Expected splat config not found: {config_file}")

    try:
        result = subprocess.run(
            ["splat"],
            cwd=cwd,
            shell=False,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout + result.stderr
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"system test failed: splat command failed with error: {error.stderr}")


def cleanup_projects(projects: list[str]) -> None:
    for project in projects:
        try:
            project_path = CLONE_DIR / project.replace("/", "-")
            shutil.rmtree(project_path, ignore_errors=True)
        except Exception as error:
            raise RuntimeError(f"Failed to remove project directory {project}: {error}")


def verify_project_cloned(project_name: str) -> Path:
    project_path = CLONE_DIR / project_name.replace("/", "-")
    if not (project_path.exists() and project_path.is_dir()):
        raise RuntimeError(f"Expected cloned project directory '{project_path}' does not exist.")
    log_success(f"Verified that project {project_name} has been cloned")
    return project_path
