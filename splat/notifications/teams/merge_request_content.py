from splat.model import AuditReport
from splat.notifications.teams.model import TeamsPayloadContentBodyElement
from splat.notifications.teams.utils import add_block_item_to_chunks, create_toggleable_text_block


def create_mr_commit_messages_notification_content(
    commit_messages: list[str],
    chunks: list[list[TeamsPayloadContentBodyElement]],
    notification_size_limit: int,
) -> list[list[TeamsPayloadContentBodyElement]]:
    index_counter = 0

    for msg in commit_messages:
        toggleable_block = create_toggleable_text_block(msg, "\f", index_counter)
        chunks = add_block_item_to_chunks(toggleable_block, chunks, notification_size_limit)
        index_counter += 1
    return chunks


def create_mr_remaning_vulns_notification_content(
    remaining_vulns: list[AuditReport],
    chunks: list[list[TeamsPayloadContentBodyElement]],
    index_counter: int,
    notification_size_limit: int,
) -> list[list[TeamsPayloadContentBodyElement]]:
    if remaining_vulns:
        chunks[-1].extend(
            [
                TeamsPayloadContentBodyElement(
                    type="TextBlock",
                    text="Remaining Vulnerable Dependencies:",
                    weight="bolder",
                    size="large",
                    color="Attention",
                ),
                TeamsPayloadContentBodyElement(
                    type="TextBlock",
                    text="These dependencies could not be resolved automatically and need manual intervention\n",
                    wrap=True,
                ),
            ]
        )

    for vuln in remaining_vulns:
        vuln_info = (
            f"{vuln.dep.name} in {vuln.lockfile.relative_path}\n"
            f"- **Installed version**: {vuln.dep.version}\n"
            f"- **Safe version**: {vuln.fixed_version}\n"
            f"- **Type of inclusion (Direct or Transitive)**: {vuln.dep.type.name}\n"
        )
        if vuln.dep.parent_deps:
            vuln_info += f"- **Parent Dependencies**: {', '.join([f'{dep.name}' for dep in vuln.dep.parent_deps])}\n"
        vuln_info += "- **Found Vulnerabilities**:\n"
        for detail in vuln.vuln_details:
            vuln_info += (
                f"  - **Vulnerability ID**: {detail.id}\n"
                f"    - **Description**: {detail.description}\n"
                f"    - **Recommendation**: {', '.join(detail.recommendation)}\n"
                f"    - **Aliases**: {', '.join(detail.aliases)}\n"
            )

        toggleable_block = create_toggleable_text_block(vuln_info, "", index_counter)
        add_block_item_to_chunks(toggleable_block, chunks, notification_size_limit)
        index_counter += 1

    return chunks
