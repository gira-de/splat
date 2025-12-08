from splat.config.model import GitConfig
from splat.git.interface import DEFAULT_GIT_AUTHOR_EMAIL, DEFAULT_GIT_AUTHOR_NAME, GitCommitAuthor
from splat.model import AuditReport, DependencyType, Severity, VulnerabilityDetail


def is_splat_author(author: GitCommitAuthor, git_cfg: GitConfig) -> bool:
    allowed_email = (git_cfg.author_email or DEFAULT_GIT_AUTHOR_EMAIL).lower()
    allowed_name = git_cfg.author_name or DEFAULT_GIT_AUTHOR_NAME
    return (author.email or "").lower() == allowed_email or author.name == allowed_name


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
