from typing import Optional

from pydantic import ValidationError

from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, Dependency, DependencyType, Lockfile, VulnerabilityDetail
from splat.package_managers.common.model import PipAuditEntry
from splat.utils.logging_utils import log_pydantic_validation_error


def parse_pip_audit_output(
    pip_audit_output: str, direct_deps: list[Dependency], lockfile: Lockfile, logger: Optional[LoggerInterface] = None
) -> list[AuditReport]:
    """
    parses the pip-audit output, returns a list of AuditReport instances, each containing details
    about a dependency, the fixed version, and vulnerability information.
    """
    audit_reports: list[AuditReport] = []
    direct_deps_dict = {dep.name: dep for dep in direct_deps}

    try:
        entry = PipAuditEntry.model_validate_json(pip_audit_output)
    except ValidationError as e:
        log_pydantic_validation_error(
            error=e,
            prefix_message="Pip Audit output Validation Failed",
            unparsable_data=pip_audit_output,
            logger=logger,
        )
        raise RuntimeError(f"Pip-audit output validation Failed: {e}")

    fix_versions = {fix.name: (fix.new_version, fix.skip_reason) for fix in entry.fixes}

    for dep in entry.dependencies:
        if not dep.vulns:
            continue

        fixed_version = None if dep.skip_reason is not None else fix_versions.get(dep.name, (None, None))[0]
        fix_skip_reason = (
            dep.skip_reason if dep.skip_reason is not None else fix_versions.get(dep.name, (None, None))[1]
        )

        dep_type = DependencyType.DIRECT if dep.name in direct_deps_dict else DependencyType.TRANSITIVE

        is_dev = direct_deps_dict.get(dep.name, Dependency(dep.name, dep_type, is_dev=False)).is_dev

        dependency = Dependency(name=dep.name, version=dep.version, type=dep_type, is_dev=is_dev)

        vuln_details = [
            VulnerabilityDetail(
                id=vuln.id,
                description=vuln.description,
                recommendation=vuln.fix_versions,
                aliases=vuln.aliases,
            )
            for vuln in dep.vulns
        ]

        report = AuditReport(
            dep=dependency,
            fixed_version=fixed_version,
            fix_skip_reason=fix_skip_reason,
            vuln_details=vuln_details,
            lockfile=lockfile,
        )
        audit_reports.append(report)

    return audit_reports
