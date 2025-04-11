from typing import Optional

from splat.notifications.teams.model import TeamsPayloadContentBodyElement
from splat.notifications.teams.utils import create_toggleable_text_block


def create_failure_notification_content(
    title: str,
    subtitle: str,
    project_url: Optional[str],
    error_summary: str,
    error_details: str,
    logfile_url: Optional[str] = None,
) -> list[TeamsPayloadContentBodyElement]:
    content: list[TeamsPayloadContentBodyElement] = [
        TeamsPayloadContentBodyElement(type="TextBlock", text=title, weight="bolder", size="extraLarge"),
        TeamsPayloadContentBodyElement(
            type="TextBlock", text=subtitle, weight="bolder", size="large", color="Attention"
        ),
    ]
    if project_url is not None:
        content.append(TeamsPayloadContentBodyElement(type="TextBlock", text=f"in [{title}]({project_url})", wrap=True))
    elif logfile_url is not None:
        content.append(
            TeamsPayloadContentBodyElement(type="TextBlock", text=f"in [View Error Logs]({logfile_url})", wrap=True)
        )
    content.append(TeamsPayloadContentBodyElement(type="TextBlock", text=error_summary, wrap=True))

    content.extend(create_toggleable_text_block(error_details, "Error Details:", 0))
    return content
