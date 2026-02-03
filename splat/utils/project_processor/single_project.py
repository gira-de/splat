import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from splat.config.config_loader import load_project_config
from splat.config.config_merger import merge_configs
from splat.config.model import Config
from splat.git.gitpython_client import GitPythonClient
from splat.git.interface import GitClientInterface
from splat.git.utils import is_splat_author
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import LocalProject, ProjectSummary, RemoteProject, Severity, StatusReport
from splat.utils.logger_config import logger, logger_manager
from splat.utils.plugin_initializer.package_managers_init import initialize_package_managers
from splat.utils.project_processor.audit_fixer import audit_and_fix_project
from splat.utils.project_processor.project_notifier import ProjectNotifier
from splat.utils.project_processor.project_operations import get_logfile_url, handle_commits


def process_local_project(project: LocalProject, config: Config, git_client: GitClientInterface) -> None:
    package_managers = initialize_package_managers(config.package_managers)
    branch_name = config.general.git.branch_name
    try:
        if git_client.is_dirty(include_untracked=True):
            logger.error(
                "Uncommitted or untracked files detected in the local project. Please stash your changes and try again."
            )
            return
    except Exception as e:
        logger.error(f"Failed to verify repository state for local project '{project.name_with_namespace}': {e}")
        return
    logger.info(f"Processing Project: {project.name_with_namespace}")
    logger.update_context(f"splat -> {project.name_with_namespace}")
    if git_client.branch_exists_local(branch_name):
        git_client.switch_branch(branch_name)
    else:
        git_client.create_branch(branch_name)
    try:
        audit_and_fix_project(project, package_managers, config, git_client)
    except Exception as e:
        logger.error(f"Error processing local project '{project.name_with_namespace}': {str(e)}")


def clone_and_process_project(
    project: RemoteProject,
    package_managers: list[PackageManagerInterface],
    git_platform: GitPlatformInterface,
    notification_sinks: list[NotificationSinksInterface],
    global_config: Config,
) -> ProjectSummary:
    try:
        project_clone_dir = Path(global_config.general.git.clone_dir).resolve() / project.name_with_namespace.replace(
            "/", "-"
        )
        if project_clone_dir.exists():
            logger.debug(f"Directory {project_clone_dir} already exists. Removing it..")
            shutil.rmtree(project_clone_dir)
        clone_url_with_token = project.clone_url.replace("https://", f"https://oauth2:{git_platform.access_token}@")
        git_client = GitPythonClient.clone(
            url=clone_url_with_token, to_path=project_clone_dir, no_single_branch=True, depth=1
        )
        project.path = project_clone_dir
        return process_remote_project(
            project, package_managers, git_platform, notification_sinks, global_config, git_client
        )
    except Exception as e:
        logger.error(f"An Error Occured while processing Project {project.name_with_namespace} : {e}")
        time_stamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%dT%H:%M:%SZ")
        return ProjectSummary(
            project_name=project.name_with_namespace,
            time_stamp=time_stamp,
            project_url=project.web_url,
            status_report=StatusReport.ERROR.value,
            severity_score=None,
            mr_url=None,
            logfile_url=get_logfile_url(),
        )


def process_remote_project(
    project: RemoteProject,
    package_managers: list[PackageManagerInterface],
    git_platform: GitPlatformInterface,
    notification_sinks: list[NotificationSinksInterface],
    global_config: Config,
    git_client: GitClientInterface,
) -> ProjectSummary:
    logger.info(f"Processing Project: {project.name_with_namespace}")
    logger.update_context(f"splat -> {project.name_with_namespace}")
    local_config = load_project_config(project.path / "splat.yaml")
    if local_config is not None:
        (merged_config, notification_sinks, package_managers) = merge_configs(
            global_config, local_config, notification_sinks, package_managers
        )
    else:
        merged_config = global_config

    notifier = ProjectNotifier(project, notification_sinks)
    logger_manager.update_logger_level(merged_config.general.logging.level)
    git_client.configure_identity(merged_config.general.git)

    branch_name = merged_config.general.git.branch_name
    default_branch = project.default_branch
    severity_score = Severity.UNKNOWN
    mr_url = None
    logfile_url = get_logfile_url()

    def _remove_project_dir() -> None:
        if not merged_config.general.debug.skip_cleanup:
            logger.debug(f"Removing {project.path}")
            shutil.rmtree(project.path)

    def _build_summary(status: StatusReport | None, severity: Severity | None, mr: str | None) -> ProjectSummary:
        time_stamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%dT%H:%M:%SZ")
        return ProjectSummary(
            project_name=project.name_with_namespace,
            time_stamp=time_stamp,
            project_url=project.web_url,
            status_report=status.value if status else None,
            severity_score=severity.name.lower() if severity else None,
            mr_url=mr,
            logfile_url=logfile_url,
        )

    branch_exists_remote = git_client.branch_exists_remote(branch_name)
    if branch_exists_remote:
        # always align local branch with remote
        git_client.create_branch(branch_name, f"origin/{branch_name}")
    else:
        git_client.create_branch(branch_name, default_branch)
    git_client.switch_branch(branch_name)
    if branch_exists_remote:
        git_client.pull(branch_name)
        open_mr_url = git_platform.get_open_merge_request_url(project, branch_name)
        commit_authors = git_client.get_commit_authors_between(default_branch, branch_name)
        non_splat_authors = [a for a in commit_authors if not is_splat_author(a, merged_config.general.git)]
        if len(non_splat_authors) > 0:
            msg = (
                f"Splat's Branch '{branch_name}' contains commit from non-splat authors: \n"
                f"Aborted processing project: '{project.name_with_namespace}' to avoid overwriting manual work."
            )
            logger.info(msg)
            _remove_project_dir()
            notifier.notify_project_skipped(msg, logfile_url)
            return _build_summary(StatusReport.MANUAL_CHANGES, severity_score, open_mr_url)
        # Only splat commits (or no commits) on the branch
        git_client.reset_branch_to_ref(branch_name, default_branch)
    try:
        audit_fix_result = audit_and_fix_project(
            project, package_managers, merged_config, git_client, notifier.notify_failure
        )
        severity_score = audit_fix_result.severity_score
        status_report, mr_url = handle_commits(
            project, audit_fix_result, branch_name, notifier, git_platform, git_client
        )

    except Exception as e:
        status_report = StatusReport.ERROR
        logger.error(f"Error processing remote project '{project.name_with_namespace}': {str(e)}")

    _remove_project_dir()
    return _build_summary(status_report, severity_score, mr_url)
