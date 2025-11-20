from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from git import Repo

from splat.config.config_loader import load_project_config
from splat.config.config_merger import merge_configs
from splat.config.model import Config
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import LocalProject, ProjectSummary, RemoteProject, Severity, StatusReport
from splat.utils.git_operations import clean_up_project_dir, clone_project
from splat.utils.logger_config import logger, logger_manager
from splat.utils.plugin_initializer.package_managers_init import initialize_package_managers
from splat.utils.project_processor.audit_fixer import audit_and_fix_project
from splat.utils.project_processor.project_notifier import ProjectNotifier
from splat.utils.project_processor.project_operations import get_logfile_url, handle_commits, log_and_checkout_project


def process_local_project(project: LocalProject, config: Config) -> None:
    package_managers = initialize_package_managers(config.package_managers)
    branch_name = config.general.git.branch_name
    try:
        repo = Repo(project.path)
        if repo.is_dirty(untracked_files=True) or bool(repo.untracked_files):
            logger.error(
                "Uncommitted or untracked files detected in the local project. "
                "Please stash your changes and try again."
            )
            return
    except Exception as e:
        logger.error(f"Failed to verify repository state for local project '{project.name_with_namespace}': {e}")
        return
    log_and_checkout_project(project, branch_name, is_local_project=True)
    try:
        audit_and_fix_project(project, package_managers, config)
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
        cloned_project = clone_project(
            project=project,
            base_clone_dir=global_config.general.git.clone_dir,
            access_token=git_platform.access_token,
        )
        p_summary = process_remote_project(
            cloned_project, package_managers, git_platform, notification_sinks, global_config
        )
    except Exception as e:
        logger.error(f"An Error Occured while processing Project {project.name_with_namespace} : {e}")
    return p_summary


def process_remote_project(
    project: RemoteProject,
    package_managers: list[PackageManagerInterface],
    git_platform: GitPlatformInterface,
    notification_sinks: list[NotificationSinksInterface],
    global_config: Config,
) -> ProjectSummary:
    branch_name = global_config.general.git.branch_name
    log_and_checkout_project(project, branch_name)

    local_config = load_project_config(project.path / "splat.yaml")
    if local_config is not None:
        (merged_config, notification_sinks, package_managers) = merge_configs(
            global_config, local_config, notification_sinks, package_managers
        )
    else:
        merged_config = global_config

    notifier = ProjectNotifier(project, notification_sinks)
    logger_manager.update_logger_level(merged_config.general.logging.level)

    severity_score: Optional[Severity] = Severity.UNKNOWN
    mr_url = None
    logfile_url = get_logfile_url()

    try:
        audit_fix_result = audit_and_fix_project(project, package_managers, merged_config, notifier.notify_failure)
        severity_score = audit_fix_result.severity_score

        status_report, mr_url = handle_commits(project, audit_fix_result, branch_name, notifier, git_platform)

    except Exception as e:
        status_report = StatusReport.ERROR
        logger.error(f"Error processing remote project '{project.name_with_namespace}': {str(e)}")

    if not merged_config.general.debug.skip_cleanup:
        clean_up_project_dir(project.path)

    time_stamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%dT%H:%M:%SZ")

    return ProjectSummary(
        project_name=project.name_with_namespace,
        time_stamp=time_stamp,
        project_url=project.web_url,
        status_report=status_report.value if status_report else None,
        severity_score=severity_score.name.lower() if severity_score else None,
        mr_url=mr_url,
        logfile_url=logfile_url,
    )
