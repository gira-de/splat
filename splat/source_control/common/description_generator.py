from splat.model import AuditReport


class DescriptionGenerator:
    def generate_commit_messages_description(self, commit_messages: list[str]) -> str:
        """Generate a description for a merge request based on commit messages and remaining vulnerabilities if
        re-auditing failed."""
        description = ""
        for msg in commit_messages:
            lines = msg.split("\n")
            first_line = lines[0]
            detail_lines = lines[1:] if len(lines) > 1 else ""
            description += f"<details>\n<summary>{first_line}</summary>\n\n"
            description += "\n".join(detail_lines) + "\n</details>\n\n"
        return description

    def generate_remaining_vulns_description(self, remaining_vulns: list[AuditReport]) -> str:
        """Generate a description for remaining vulnerabilities."""
        description = ""
        if len(remaining_vulns) > 0:
            description += "**Remaining Vulnerable dependencies:**"
            description += "\n\nThese dependencies could not be resolved automatically and need manual intervention\n"
            for vuln in remaining_vulns:
                description += (
                    f"<details>\n<summary>"
                    f"{vuln.dep.name} in {vuln.lockfile.relative_path}</summary>\n\n"
                    f"  - **Installed version**: {vuln.dep.version}\n"
                    f"  - **Safe version**: {vuln.fixed_version}\n"
                    f"  - **Type of inclusion (Direct or Transitive)**: {vuln.dep.type.name}\n"
                )
                description += (
                    f"  - **Parent Dependencies**: {', '.join([f'{dep.name}' for dep in vuln.dep.parent_deps])}\n"
                    if vuln.dep.parent_deps
                    else ""
                )
                description += "  - **Found Vulnerabilities**:\n"
                for detail in vuln.vuln_details:
                    description += (
                        f"  <details>\n<summary>{detail.id}</summary>\n\n"
                        f"  - **Vulnerability ID**: {detail.id}\n\n"
                        f"  - **Description**: {detail.description}\n\n"
                        f"  - **Recommendation**: {', '.join(detail.recommendation)}\n\n"
                        f"  - **Aliases**: {', '.join(detail.aliases)}\n\n"
                        "   </details>\n"
                    )
                description += "</details>\n\n"

        return description
