from typing import Any, Literal

import pyfiglet
from pydantic import ValidationError

from splat.config.model import FiltersConfig, GeneralConfig, HooksConfig
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, Lockfile, ProjectAuditFixResult
from splat.utils.logger_config import ContextLoggerAdapter, default_logger, logger


def generate_banner(text: str) -> str:
    result: str = pyfiglet.figlet_format(text)
    return result


def log_general_config(general_config: GeneralConfig | None, logger: LoggerInterface) -> None:
    if general_config is None:
        logger.info("No project-specific general configuration provided. Using global configuration.")
        return
    lines = [
        f"Logging level: {general_config.logging.level}",
        f"Git clone directory: {general_config.git.clone_dir}",
        f"Git branch name: {general_config.git.branch_name}",
        f"Debug - Skip cleanup: {general_config.debug.skip_cleanup}",
    ]
    logger.debug("Using general configuration:\n" + "\n".join(lines))


def log_hooks_config(hooks_config: HooksConfig | None, logger: LoggerInterface) -> None:
    if hooks_config is None:
        logger.info("No hooks configuration provided. Skipping hooks..")
        return None

    for hook_type, hooks in hooks_config.__dict__.items():
        lines = []
        for pattern, config in hooks.items():
            pattern_type = "glob" if "*" in pattern or "?" in pattern else "regex"
            commands = " && ".join(config.script)
            cwd = config.cwd
            separate_exec = " (executes separately for each file)" if config.one_command_per_file else ""
            lines.append(f'{pattern} (using {pattern_type}): executes "{commands}" in {cwd}{separate_exec}')

        if lines:
            logger.debug(
                f"You have {len(hooks)} {hook_type.replace('_', ' ').title()} hooks configured:\n" + "\n".join(lines)
            )

        logger.info(
            f"Configured {len(hooks)} {hook_type.replace('_', ' ').title()} Hooks,"
            f' with patterns: "{", ".join(hooks.keys())}"'
        )


def log_found_lockfiles(
    manager_name: str,
    project_name: str,
    found_lockfiles: list[Lockfile],
) -> None:
    if len(found_lockfiles) == 0:
        logger.info(f"No {manager_name} lockfiles found in {project_name}. Skipping...")
    else:
        lockfiles_str = "\n    - ".join([str(lock_file.relative_path) for lock_file in found_lockfiles])
        logger.info(f"Found lockfiles by {manager_name} in {project_name}:\n    - {lockfiles_str}")


def log_found_audit_reports(
    found_lockfile: Lockfile,
    vulnerable_dependencies: list[AuditReport],
) -> None:
    if not vulnerable_dependencies:
        logger.info(f"No vulnerabilities found in {found_lockfile.relative_path}.")
    else:
        logger.info(
            f"Audit completed. Found {len(vulnerable_dependencies)} vulnerable dependencies in "
            f"{found_lockfile.relative_path}: "
            + ", ".join([f"{vuln.dep.name} ({vuln.dep.type.name})" for vuln in vulnerable_dependencies])
        )


def format_commit_summary(commit_messages: list[str]) -> str:
    if not commit_messages:
        return ""
    return "Commit summary:\n    - " + "\n    - ".join([msg.split("\n")[0] for msg in commit_messages])


def log_audit(logger: ContextLoggerAdapter, lockfile: Lockfile, re_audit: bool) -> None:
    action = "Reauditing" if re_audit else "Auditing"
    logger.info(f"{action} dependencies in lockfile '{lockfile.relative_path}' for security vulnerabilities...")


def format_remaining_vulns_summary(remaining_vulns: list[AuditReport]) -> str:
    if not remaining_vulns:
        return "No remaining vulnerabilities."
    vuln_summary = "\n    - ".join([f"{vuln.dep.name} in {vuln.lockfile.relative_path}" for vuln in remaining_vulns])
    return (
        f"Post-update audit failed. Found {len(remaining_vulns)} remaining vulnerable dependencies"
        f":\n    - {vuln_summary}"
    )


def log_audit_fix_results(project_name: str, branch_name: str, result: ProjectAuditFixResult) -> None:
    commit_summary = format_commit_summary(result.commit_messages)
    remaining_vulns_summary = format_remaining_vulns_summary(result.remaining_vulns)

    if result.commit_messages and result.remaining_vulns:
        # Case 1: Vulnerabilities were fixed, but some still remain
        logger.info(
            f"[SUMMARY] Some vulnerabilities were fixed and changes were committed to branch '{branch_name}' for "
            f"project '{project_name}', but some vulnerabilities could not be automatically fixed.\n"
            f"{commit_summary}\n"
            f"{remaining_vulns_summary}"
        )
    elif not result.commit_messages and result.remaining_vulns:
        # Case 2: Some vulnerabilities remain, but no changes were made
        logger.info(
            f"[SUMMARY] Audit completed for project '{project_name}', but no fixes were made. "
            f"Some vulnerabilities could not be automatically fixed.\n"
            f"{remaining_vulns_summary}"
        )
    elif result.commit_messages and not result.remaining_vulns:
        # Case 3: All vulnerabilities fixed
        logger.info(
            f"[SUMMARY] All identified vulnerabilities were fixed and changes were committed to branch '{branch_name}' "
            f"for project '{project_name}'.\n"
            f"{commit_summary}"
        )
    else:
        # Case 4: No vulnerabilities found or fixed (clean)
        logger.info(f"[SUMMARY] No vulnerabilities found, project '{project_name}' is clean.")


def format_filters_log(filters: FiltersConfig) -> str:
    if filters.exclude or filters.include:
        filters_log = f"filters:\nExclude: [{', '.join(filters.exclude)}]\nInclude: [{', '.join(filters.include)}]"
    else:
        filters_log = "no filters"
    return filters_log


def log_pydantic_validation_error(
    error: ValidationError,
    prefix_message: str,
    unparsable_data: str | dict[Any, Any] | None,
    logger: LoggerInterface | None = None,
) -> None:
    logger = logger or default_logger
    error_details = "; ".join(
        (f"Field '{' -> '.join(str(item) for item in e['loc'])}' - {e['msg']}" if e["loc"] else f"Error - {e['msg']}")
        for e in error.errors()
    )
    if unparsable_data is not None:
        data_details = f"\nWhile trying to parse:\n{unparsable_data}"
    else:
        data_details = ""
    logger.error(f"{prefix_message}: {error_details}{data_details}")


def log_configured_package_managers(pms: dict[str, bool], logger: LoggerInterface) -> None:
    enabled_count = sum(1 for enabled in pms.values() if enabled)
    disabled_count = len(pms) - enabled_count
    status_summary = ", ".join(
        [f"{pm_name}: {'Enabled' if enabled else 'Disabled'}" for pm_name, enabled in pms.items()]
    )
    logger.info(f"Configured package managers: {enabled_count} enabled, {disabled_count} disabled ({status_summary})")


def log_missing_credentials(logger: LoggerInterface, repo_name: str) -> None:
    logger.debug(f"No credentials provided for repository '{repo_name}', skipping authentication.")


def log_invalid_credentials(logger: LoggerInterface, repo_name: str) -> None:
    logger.debug(f"Invalid credentials provided for repository '{repo_name}', skipping authentication.")


def log_authentication_type(logger: LoggerInterface, repo_name: str, auth_type: Literal["token", "HTTP basic"]) -> None:
    logger.debug(f"Configuring {auth_type} authentication for '{repo_name}'.")
