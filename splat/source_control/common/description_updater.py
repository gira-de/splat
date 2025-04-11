class DescriptionUpdater:
    def update_existing_description(
        self,
        existing_description: str,
        new_commit_messages_part: str,
        new_remaining_vulns_part: str,
    ) -> str:
        """Update the existing description with the new description part."""

        def insert_after_marker(description: str, marker: str, new_part: str, replace: bool = False) -> str:
            marker_pos = description.find(marker)
            if marker_pos == -1:
                return f"{description}\n\n{marker}\n\n{new_part}"
            insert_pos = marker_pos + len(marker) + 1
            if replace:
                return f"{description[:insert_pos]}{new_part}"
            return f"{description[:insert_pos]}{new_part}{description[insert_pos:]}"

        updated_description = existing_description
        # Update commit messages part
        if new_commit_messages_part != "":
            updated_description = insert_after_marker(
                existing_description, "**Updates Summary:**", new_commit_messages_part
            )

        # Update remaining vulnerabilities part if provided
        if new_remaining_vulns_part != "":
            updated_description = insert_after_marker(
                updated_description,
                "**Remaining Vulnerable dependencies:**",
                new_remaining_vulns_part.removeprefix("**Remaining Vulnerable dependencies:**\n\n"),
                True,
            )

        return updated_description
