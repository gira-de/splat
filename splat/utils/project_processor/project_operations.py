import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from splat.git.interface import GitClientInterface
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.model import ProjectAuditFixResult, ProjectSummary, RemoteProject, StatusReport
from splat.utils.logger_config import logger
from splat.utils.project_processor.project_notifier import ProjectNotifier


def export_json_summary(
    project_summaries: list[ProjectSummary],
    json_path: Path = Path("dashboard/projects_summary.json"),
) -> None:
    logger.debug(f"Exporting Project(s) summary to {json_path}")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    project_summaries_dicts = [asdict(summary) for summary in project_summaries]
    with open(json_path, "w") as json_file:
        json.dump(project_summaries_dicts, json_file, indent=2)
    logger.info(f"Project(s) summary successfully exported to {json_path}")


def get_logfile_url() -> Optional[str]:
    """Determine the log file url based on the environment (GitLab CI, GitHub Actions, local, etc.)."""

    # Check if running in GitLab CI
    gitlab_job_url = os.getenv("CI_JOB_URL")
    if gitlab_job_url:
        return gitlab_job_url

    # Check if running in GitHub Actions
    github_run_url = os.getenv("GITHUB_SERVER_URL")
    github_repo = os.getenv("GITHUB_REPOSITORY")
    github_run_id = os.getenv("GITHUB_RUN_ID")
    if github_run_url and github_repo and github_run_id:
        return f"{github_run_url}/{github_repo}/actions/runs/{github_run_id}"

    # running locally or in another unknown environment
    return None


def handle_commits(
    project: RemoteProject,
    project_result: ProjectAuditFixResult,
    branch_name: str,
    notifier: ProjectNotifier,
    git_platform: GitPlatformInterface,
    git_client: GitClientInterface,
) -> tuple[StatusReport, Optional[str]]:
    """Handle the commit actions for remote projects."""

    commits = project_result.commit_messages
    remaining_vulns = project_result.remaining_vulns
    project_status = project_result.status_report

    if not commits and not remaining_vulns:
        logger.info("No vulnerabilities fixed, not pushing any changes")
        return project_status, None

    git_client.push(branch_name)

    try:
        logger.update_context(f"splat -> {project.name_with_namespace} -> {git_platform.type}")
        mr_result = git_platform.create_or_update_merge_request(project, commits, branch_name, remaining_vulns)
        notifier.notify_mr_success(mr_result, commits, remaining_vulns)
    except Exception as e:
        context = f"{git_platform.merge_request_type} Request Creation or Update on {git_platform.type}"
        notifier.notify_failure(context, e)
        return StatusReport.ERROR, None

    if project_status == StatusReport.ERROR:
        final_status = StatusReport.ERROR
    elif remaining_vulns:
        final_status = StatusReport.VULNS_LEFT
    else:
        final_status = StatusReport.MR_PENDING

    return final_status, mr_result.url
