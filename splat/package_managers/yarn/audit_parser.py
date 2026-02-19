from pydantic import ValidationError

from splat.interface.logger import LoggerInterface
from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    Severity,
    VulnerabilityDetail,
)
from splat.package_managers.yarn.model import YarnAuditEntry
from splat.utils.logging_utils import log_pydantic_validation_error


def _get_severity_enum(severity_str: str) -> Severity:
    severity_map = {
        "low": Severity.LOW,
        "moderate": Severity.MODERATE,
        "high": Severity.HIGH,
        "critical": Severity.CRITICAL,
    }

    return severity_map.get(severity_str.lower(), Severity.UNKNOWN)


def parse_yarn_audit_output(output: str, lockfile: Lockfile, logger: LoggerInterface) -> list[AuditReport]:
    """
    Parses the output from `yarn audit --json` and extracts information about each vulnerability,
    returning a list of AuditReport instances.
    """
    aggregated_reports: dict[str, AuditReport] = {}
    output_strip = output.strip()
    if not output_strip:
        raise RuntimeError("Yarn audit output was empty or invalid. No vulnerabilities found.")

    rows = output_strip.split("\n")
    for line in rows[:-1]:
        try:
            entry = YarnAuditEntry.model_validate_json(line)

            advisory = entry.data.advisory
            resolution = entry.data.resolution

            dep_type = DependencyType.TRANSITIVE if len(resolution.path.split(">")) > 1 else DependencyType.DIRECT
            fixed_version = advisory.patched_versions.strip(">=<>")
            vulnerable_version = advisory.findings[0].version
            dependency_name = advisory.module_name
            severity_str = advisory.severity if advisory.severity else "unknown"
            severity = _get_severity_enum(severity_str)

            dependency = Dependency(name=dependency_name, version=vulnerable_version, type=dep_type)

            vuln_detail = VulnerabilityDetail(
                id=advisory.github_advisory_id,
                description=advisory.overview,
                recommendation=[advisory.recommendation],
                aliases=advisory.cves,
            )

            if dependency_name in aggregated_reports:
                existing_report = aggregated_reports[dependency_name]
                vuln_details = existing_report.vuln_details
                if not any(vd.id == vuln_detail.id for vd in vuln_details):
                    existing_report.vuln_details.append(vuln_detail)
                if existing_report.fixed_version is not None:
                    fixed_version = max(
                        existing_report.fixed_version,
                        fixed_version,
                        key=lambda v: [int(x) for x in v.split(".") if x.isdigit()],
                    )

                if existing_report.dep.type != dep_type:
                    dep_type = DependencyType.BOTH
                    dependency.type = dep_type

                updated_report = AuditReport(
                    dep=dependency,
                    severity=severity,
                    fixed_version=fixed_version,
                    vuln_details=vuln_details,
                    lockfile=lockfile,
                )
                aggregated_reports[dependency_name] = updated_report

            else:
                aggregated_reports[dependency_name] = AuditReport(
                    dep=dependency,
                    severity=severity,
                    fixed_version=fixed_version,
                    vuln_details=[vuln_detail],
                    lockfile=lockfile,
                )

        except ValidationError as e:
            msg = f"Yarn Audit output Validation Failed at line {line}"
            log_pydantic_validation_error(error=e, prefix_message=msg, unparsable_data=output, logger=logger)
            raise RuntimeError(f"{msg}: {e}")

    return list(aggregated_reports.values())
