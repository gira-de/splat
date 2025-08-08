import shutil
from pathlib import Path

from git.repo import Repo

from splat.model import AuditReport, DependencyType, RemoteProject, Severity, VulnerabilityDetail
from splat.utils.errors import GitOperationError
from splat.utils.logger_config import logger


def clone_project(project: RemoteProject, base_clone_dir: str, access_token: str) -> RemoteProject:
    project_clone_dir = Path(base_clone_dir).resolve() / project.name_with_namespace.replace("/", "-")

    clone_url_with_token = project.clone_url.replace("https://", f"https://oauth2:{access_token}@")

    if project_clone_dir.exists():
        logger.debug(f"Directory {project_clone_dir} already exists. Removing it..")
        try:
            shutil.rmtree(project_clone_dir)
        except PermissionError as e:
            logger.error(e)
    try:
        logger.debug(f"Cloning {project.name_with_namespace} into {project_clone_dir}")
        Repo.clone_from(url=clone_url_with_token, to_path=project_clone_dir, no_single_branch=True)
        project.path = project_clone_dir
        logger.info(f"Successfully cloned {project.name_with_namespace} into {project.path}")
    except Exception as e:
        raise GitOperationError(f"Failed to clone {project_clone_dir} into {project.path}", e)
    return project


def discard_files_changes(repo_path: Path, files_to_discard: list[str] | None = None) -> None:
    """
    Discards changes in a given Git repository. If files_to_discard is provided,
    only those files will have their changes discarded. Otherwise, all changes
    will be discarded."""
    logger.debug(f"Discarding all modified and untracked files in {repo_path}")
    try:
        repo = Repo(repo_path, search_parent_directories=True)
        if files_to_discard:
            repo.git.checkout("--", *files_to_discard)
            logger.info(f"Changes in the file(s) {', '.join(files_to_discard)} have been discarded.")
        else:
            repo.git.reset("--hard")
            repo.git.clean("-fd")
            logger.debug("All changes in other files have been discarded.")
    except Exception as e:
        logger.error(f"Failed to discard local changes: {e}")


def checkout_branch(repo_path: Path, branch_name: str, is_local_project: bool = False) -> None:
    """Checks out the specified branch if it exists, or creates it if it does not."""
    try:
        repo = Repo(repo_path, search_parent_directories=True)
        main_branch_name = repo.git.symbolic_ref("refs/remotes/origin/HEAD").split("/")[-1]
        logger.debug(f"Checking out branch '{main_branch_name}' to '{branch_name}' in repository '{repo_path.name}'")

        branch_exists = branch_name in (repo.heads if is_local_project else repo.remote().refs)

        if branch_exists is True:
            repo.git.switch(branch_name)
            if is_local_project is False:
                repo.git.checkout(branch_name)
                repo.remote().pull(branch_name)
                logger.info(
                    f"Checked out and pulled from existing remote branch '{branch_name}' "
                    f"in repository '{repo_path.name}' (default branch: '{main_branch_name}')"
                )
            else:
                logger.info(
                    f"Checked out existing local branch '{branch_name}' in repository '{repo_path.name}' "
                    f"(default branch: '{main_branch_name}')"
                )
        else:
            repo.git.checkout("HEAD", b=branch_name)
            logger.info(
                f"Created and checked out new branch '{branch_name}' in repository '{repo_path.name}' "
                f"(from default branch: '{main_branch_name}')"
            )
    except Exception as e:
        logger.error(f"Failed to checkout, pull, or create branch '{branch_name}' in repository '{repo_path}': {e}")


def _get_severity_emoji(severity: Severity) -> str:
    severity_emoji_map = {
        Severity.LOW: "🟡",
        Severity.MODERATE: "🟠",
        Severity.HIGH: "🔴",
        Severity.CRITICAL: "🚨",
        Severity.UNKNOWN: "❓",
    }
    return severity_emoji_map.get(severity, "❓")


def _format_vulnerability_details(vuln_detail: VulnerabilityDetail) -> str:
    return (
        f"- {vuln_detail.description}\n"
        f"  - Aliases: {', '.join(vuln_detail.aliases)}\n"
        f"  - Recommendation: {', '.join(vuln_detail.recommendation)}\n\n"
    )


def create_commit_message(vuln_report: AuditReport) -> str:
    folder_display = str(vuln_report.lockfile.relative_path)
    first_line = ""
    severity = ""

    if vuln_report.severity != Severity.UNKNOWN:
        severity_emoji = _get_severity_emoji(vuln_report.severity)
        severity = f" [{vuln_report.severity.name.lower()} {severity_emoji}]"

    if vuln_report.dep.type == DependencyType.TRANSITIVE and vuln_report.dep.parent_deps:
        parents_with_versions = []
        for parent_dep in vuln_report.dep.parent_deps:
            if parent_dep.version is not None:
                version = f"~={parent_dep.version}.0"
                parents_with_versions.append(f"{parent_dep.name} to {version}")

        parents_with_versions_str = ", ".join(parents_with_versions)

        first_line = (
            f"fix: Security{severity}: Update {parents_with_versions_str} to fix {vuln_report.dep.name} "
            f"in {folder_display}"
        )

    else:
        first_line = (
            f"fix: Security{severity}: Update {vuln_report.dep.name} from {vuln_report.dep.version} "
            f"to {vuln_report.fixed_version} in {folder_display}"
        )

    body_lines = ["This update addresses the following vulnerabilities:\n\n"]

    for vuln_detail in vuln_report.vuln_details:
        body_lines.append(_format_vulnerability_details(vuln_detail))

    return first_line + "\n\n" + "".join(body_lines)


def commit_changes(repo: Repo, files_to_commit: list[str], report: AuditReport) -> str:
    if not files_to_commit:
        raise ValueError("No files to commit.")

    logger.debug(f'Committing files {", ".join(str(file) for file in files_to_commit)} in {repo.working_dir}')
    try:
        # Check if there are actual changes staged for commit
        repo.index.add([str(file) for file in files_to_commit])
        if not repo.index.diff("HEAD"):
            logger.debug("No changes to commit. Skipping commit.")
            return ""
        # Proceed with committing changes
        commit_message = create_commit_message(report)
        repo.index.commit(message=commit_message)
        first_line = commit_message.split("\n", 1)[0]
        logger.info(f"Committed changes: {first_line}")

        return commit_message
    except Exception as e:
        raise GitOperationError("Failed to commit changes", e)


def push_changes(repo_path: Path, branch_name: str, remote_name: str = "origin") -> None:
    logger.info(f"Pushing changes in {repo_path} for branch {branch_name}")
    try:
        repo = Repo(repo_path)
        remote = repo.remote(name=remote_name)

        push_info = remote.push(refspec=f"{branch_name}:{branch_name}")

        for info in push_info:
            if info.flags & info.ERROR:
                logger.error(f"Push failed: {info.summary}")
            else:
                logger.debug(f"Pushed {info.local_ref} to {info.remote_ref}")
    except ValueError as e:
        raise ValueError(f"Remote '{remote_name}' not found in repository: {e}")
    except Exception as e:
        raise GitOperationError("An error occurred while pushing changes", e)


def clean_up_project_dir(project_dir: Path) -> None:
    try:
        logger.debug(f"Removing {project_dir.name}")
        shutil.rmtree(project_dir)
    except Exception as e:
        logger.error(f"Failed to remove project directory {project_dir.name}: {e}")


def is_git_ignored(file_path: str, repo_path: Path) -> bool:
    repo = Repo(repo_path)
    try:
        result = repo.git.check_ignore(file_path)
        return bool(result)
    except Exception:
        return False
