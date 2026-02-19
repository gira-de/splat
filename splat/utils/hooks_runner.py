import re
import shlex
import subprocess  # nosec B404
from pathlib import Path

from splat.config.model import HooksPreCommitConfig
from splat.interface.logger import LoggerInterface
from splat.model import Lockfile


def _is_regex(pattern: str) -> bool:
    return pattern.startswith("/") and pattern.endswith("/")


def _replace_placeholders(content: str, replacements: dict[str, str]) -> str:
    """
    Replace placeholders in the script with actual values from replacements.

    :param script: The script command list with placeholders.
    :param replacements: A dictionary of placeholders and their corresponding replacement values.
    :return: The script with placeholders replaced.
    """
    # Convert ${PLACEHOLDER} to {PLACEHOLDER}
    content = re.sub(r"\$\{(\w+)\}", r"{\1}", content)
    replacements = {re.sub(r"\$\{(\w+)\}", r"\1", key): value for key, value in replacements.items()}
    return content.format(**replacements)


def run_pre_commit_hooks(
    changed_files: list[str],
    pre_commit_hooks_config: dict[str, HooksPreCommitConfig],
    lockfile: Lockfile,
    manifestfile: Path,
    project_root: Path,
    logger: LoggerInterface,
) -> None:
    """
    Run pre-commit hooks for the given files based on the pre-commit hooks configuration.

    :param changed_files: List of files that have been changed and are about to be committed.
    :param pre_commit_hooks_config: The pre-commit hooks configuration, mapping file patterns to hook scripts.
    :param lockfile: The lockfile model that is being processed (to replace placeholders).
    :param manifestfile: The path to the manifest file (to replace placeholders).
    :param project_root: The root directory of the project (to replace placeholders).
    """
    base_replacements = {
        "${SPLAT_MANIFEST_FILE}": str(manifestfile.resolve()),
        "${SPLAT_LOCK_FILE}": str(lockfile.path.resolve()),
        "${SPLAT_PROJECT_ROOT}": str(project_root.resolve()),
        "${SPLAT_PACKAGE_ROOT}": str(lockfile.path.parent.resolve()),
    }

    for pattern, single_pre_commit_hook_config in pre_commit_hooks_config.items():
        matched_files: list[str] = []

        for file in changed_files:
            try:
                if _is_regex(pattern):
                    regex_pattern = pattern[1:-1]
                    if re.match(regex_pattern, file):
                        matched_files.append(file)
                else:  # glob pattern matching
                    if Path(file).match(pattern):
                        matched_files.append(file)
            except re.error as regex_error:
                logger.error(f"Invalid regex pattern '{pattern}': {regex_error}")
                continue

        if len(matched_files) > 0:
            replacements = {
                **base_replacements,
                "${SPLAT_MATCHED_FILES}": " ".join([str(Path(mf).resolve()) for mf in matched_files]),
            }
            logger.info(
                f"Running pre-commit hook for pattern '{pattern}' with {len(matched_files)} "
                f"matched file(s): {', '.join(mf for mf in matched_files)}"
            )
            run_pre_commit_script(single_pre_commit_hook_config, replacements, logger)
        else:
            logger.info(f"No matching files found for pre-commit hook pattern '{pattern}'. Skipping...")


def run_pre_commit_script(
    pre_commit_hook_config: HooksPreCommitConfig, replacements: dict[str, str], logger: LoggerInterface
) -> None:
    try:
        cwd = Path(_replace_placeholders(pre_commit_hook_config.cwd, replacements)).resolve()

        for cmd in pre_commit_hook_config.script:
            if pre_commit_hook_config.one_command_per_file is True and "${SPLAT_MATCHED_FILES}" in cmd:
                matched_files = replacements["${SPLAT_MATCHED_FILES}"].split()

                for single_file in matched_files:
                    single_replacement = {
                        **replacements,
                        "${SPLAT_MATCHED_FILES}": single_file,
                    }
                    formatted_command = _replace_placeholders(cmd, single_replacement)
                    logger.debug(
                        f"Running Pre Commit Hook Script Command for file {single_file}:"
                        f" \n  - {formatted_command} in {cwd}"
                    )
                    result = subprocess.run(
                        shlex.split(formatted_command),
                        cwd=cwd,
                        shell=False,  # nosec
                        check=True,
                        stdout=subprocess.PIPE,
                    )
                    logger.debug("\n" + result.stdout.decode("utf-8"))
                    logger.info(f"Successfully ran the Command: {formatted_command} in {cwd}")
            else:
                formatted_command = _replace_placeholders(cmd, replacements)
                logger.debug(f"Running Pre Commit Hook Script Command: {formatted_command} in {cwd}")
                result = subprocess.run(
                    shlex.split(formatted_command),
                    cwd=cwd,
                    shell=False,  # nosec
                    check=True,
                    stdout=subprocess.PIPE,
                )
                logger.debug("\n" + result.stdout.decode("utf-8"))
                logger.info(f"Successfully ran the Command: {formatted_command} in {cwd}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Pre-commit hook script '{pre_commit_hook_config.script}' failed with error: {e}")
