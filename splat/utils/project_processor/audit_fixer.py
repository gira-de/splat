from contextlib import contextmanager
from typing import Callable, Generator, Optional

from splat.config.model import Config
from splat.git.interface import GitClientInterface
from splat.git.utils import create_commit_message
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.model import AuditReport, Lockfile, Project, ProjectAuditFixResult, Severity, StatusReport
from splat.utils.errors import SkipLockfileProcessingError
from splat.utils.hooks_runner import run_pre_commit_hooks
from splat.utils.logger_config import ContextLoggerAdapter
from splat.utils.logger_config import logger as production_logger
from splat.utils.logging_utils import (
    format_remaining_vulns_summary,
    log_audit,
    log_audit_fix_results,
    log_found_audit_reports,
)


@contextmanager
def handle_project_errors(
    project: Project,
    context: str,
    status_report: list[StatusReport],
    notify_callback: Optional[Callable[[str, Exception, Optional[AuditReport]], None]] = None,
    report: Optional[AuditReport] = None,
    skip_loop: bool = True,
) -> Generator[None, None, None]:
    """
    A context manager to handle project-specific errors, logging, and notifications.

    Args:
        project: The project where the error occurred.
        context: A description of the context or operation where the error happened.
        status_report: A mutable list containing the status of the process.
        notify_callback: Optional callback for sending notifications.
        report: Optional audit report for dependency update failures.
        skip_loop: If True, re-raises a custom exception to skip the current lockfile.
    """
    try:
        yield
    except Exception as error:
        production_logger.error(f"Error in {context} for project '{project.name_with_namespace}': {error}")
        if notify_callback:
            notify_callback(context, error, report)
        status_report[0] = StatusReport.ERROR
        if skip_loop:
            raise SkipLockfileProcessingError from error


def audit_and_fix_project(
    project: Project,
    package_managers: list[PackageManagerInterface],
    config: Config,
    git_client: GitClientInterface,
    notify_callback: Optional[Callable[[str, Exception, Optional[AuditReport]], None]] = None,
    logger: ContextLoggerAdapter = production_logger,
) -> ProjectAuditFixResult:
    commit_messages: list[str] = []
    remaining_vulns: list[AuditReport] = []
    highest_severity: Optional[Severity] = None
    status_report = [StatusReport.CLEAN]  # mutable

    for manager in package_managers:
        logger.update_context(f"splat -> {project.name_with_namespace} -> {manager.name}")
        found_lockfiles: list[Lockfile] = manager.find_lockfiles(project)
        found_lockfiles = [lf for lf in found_lockfiles if not git_client.is_ignored(str(lf.path))]

        for found_lockfile in found_lockfiles:
            try:
                audit_reports: Optional[list[AuditReport]] = None

                # Install deps
                with handle_project_errors(project, "Installing dependencies", status_report, notify_callback):
                    manager.install(found_lockfile)

                # Audit lockfile
                with handle_project_errors(project, "Auditing lockfile", status_report, notify_callback):
                    log_audit(logger, found_lockfile, False)
                    audit_reports = manager.audit(found_lockfile)
                    log_found_audit_reports(found_lockfile, audit_reports)

                if not audit_reports:
                    continue

                for report in audit_reports:
                    files_to_commit: Optional[list[str]] = None
                    if highest_severity is None or report.severity.value > highest_severity.value:
                        highest_severity = report.severity

                    # Dependency Update
                    with handle_project_errors(
                        project, "Dependency Update", status_report, notify_callback, report, skip_loop=False
                    ):
                        files_to_commit = manager.update(report)

                    if not files_to_commit:
                        continue

                    # Pre-commit Hooks
                    with handle_project_errors(
                        project, "Running pre-commit hooks", status_report, notify_callback, report
                    ):
                        run_pre_commit_hooks(
                            changed_files=files_to_commit,
                            pre_commit_hooks_config=config.hooks.pre_commit,
                            lockfile=found_lockfile,
                            manifestfile=found_lockfile.path.parent / manager.manifest_file_name,
                            project_root=project.path,
                        )

                    # Commit Changes
                    commit_message = create_commit_message(report)
                    if git_client.commit_files(files_to_commit, commit_message):
                        commit_messages.insert(0, commit_message)
                    git_client.discard_changes()

                if commit_messages:
                    with handle_project_errors(
                        project, "Re-auditing lockfile", status_report, notify_callback, skip_loop=False
                    ):
                        log_audit(logger, found_lockfile, True)
                        vulns = manager.audit(found_lockfile, re_audit=True)
                        remaining_vulns.extend(vulns)
                        logger.info(format_remaining_vulns_summary(vulns))
                else:
                    remaining_vulns = audit_reports

            except SkipLockfileProcessingError:
                continue

    logger.update_context(f"splat -> {project.name_with_namespace}")
    branch_name = config.general.git.branch_name
    audit_fix_result = ProjectAuditFixResult(highest_severity, commit_messages, remaining_vulns, status_report[0])
    log_audit_fix_results(project.name_with_namespace, branch_name, audit_fix_result)
    return audit_fix_result
