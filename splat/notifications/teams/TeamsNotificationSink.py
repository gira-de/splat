from __future__ import annotations

from typing import Optional

import requests

from splat.config.model import SinkConfig
from splat.interface.logger import LoggerInterface
from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.notifications.teams.failure_content import create_failure_notification_content
from splat.notifications.teams.merge_request_content import (
    create_mr_commit_messages_notification_content,
    create_mr_remaning_vulns_notification_content,
)
from splat.notifications.teams.model import (
    MSTeams,
    TeamsPayload,
    TeamsPayloadAttachment,
    TeamsPayloadContent,
    TeamsPayloadContentBodyElement,
    TeamsSinkConfig,
)
from splat.utils.env_manager.interface import EnvManager
from splat.utils.env_manager.os import OsEnvManager
from splat.utils.logger_config import default_logger


class TeamsNotificationSink(NotificationSinksInterface):
    def __init__(
        self,
        config: TeamsSinkConfig,
        logger: Optional[LoggerInterface] = None,
        env_manager: Optional[EnvManager] = None,
        post_size_limit: int = 20000,
    ) -> None:
        super().__init__(config)
        self.logger = logger or default_logger
        self.env_manager = env_manager or OsEnvManager(self.logger)
        self.general_webhook_url = self.env_manager.resolve_value(config.webhook_url)
        self.mr_webhook_url = (
            self.env_manager.resolve_value(config.merge_request.webhook_url) if config.merge_request else None
        )
        self.update_failure_webhook_url = (
            self.env_manager.resolve_value(config.update_failure.webhook_url) if config.update_failure else None
        )
        self.error_webhook_url = self.env_manager.resolve_value(config.error.webhook_url) if config.error else None
        self.notification_size_limit = post_size_limit

    @property
    def type(self) -> str:
        return "teams"

    @classmethod
    def from_sink_config(cls, sink_config: SinkConfig) -> TeamsNotificationSink:
        config_dict = sink_config.model_dump()
        validated_config = TeamsSinkConfig.model_validate(config_dict)
        return cls(config=validated_config)

    def _send_notification(
        self, webhook_url: str, body_chunks: list[list[TeamsPayloadContentBodyElement]], timeout: float = 5.0
    ) -> None:
        headers = {"Content-Type": "application/json"}
        for chunk in body_chunks:
            payload = TeamsPayload(
                type="message",
                attachments=[
                    TeamsPayloadAttachment(
                        contentType="application/vnd.microsoft.card.adaptive",
                        content=TeamsPayloadContent(
                            schema_="https://adaptivecards.io/schemas/adaptive-card.json",
                            msteams=MSTeams(width="Full"),
                            type="AdaptiveCard",
                            version="1.5",
                            body=chunk,
                        ),
                    )
                ],
            )
            try:
                response = requests.post(
                    webhook_url,
                    json=payload.model_dump(by_alias=True, exclude_unset=True),
                    headers=headers,
                    timeout=timeout,
                )

                response.raise_for_status()
                self.logger.info("Notification sent successfully")
            except requests.Timeout:
                self.logger.error("Failed to send Teams notification: Timeout error occurred")
            except requests.HTTPError as http_err:
                self.logger.error(f"Failed to send Teams notification: HTTP error occurred: {http_err}")
            except requests.RequestException as req_err:
                self.logger.error(f"Failed to send Teams notification: Request error occurred: {req_err}")

    def send_merge_request_notification(
        self, merge_request: MergeRequest, commit_messages: list[str], remaining_vulns: list[AuditReport]
    ) -> None:
        self.logger.debug(f"Sending notification: {merge_request.operation} for: {merge_request.project_name}")
        subtitle = f"{merge_request.operation}: [{merge_request.title}]({merge_request.url})"
        current_content_chunk: list[TeamsPayloadContentBodyElement] = [
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                text=merge_request.project_name,
                weight="bolder",
                size="extraLarge",
            ),
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                size="large",
                text=subtitle,
            ),
            TeamsPayloadContentBodyElement(
                type="TextBlock",
                text=f"in [{merge_request.project_name}]({merge_request.project_url})",
            ),
        ]

        chunks: list[list[TeamsPayloadContentBodyElement]] = [current_content_chunk]

        chunks = create_mr_commit_messages_notification_content(commit_messages, chunks, self.notification_size_limit)

        if remaining_vulns:
            chunks = create_mr_remaning_vulns_notification_content(
                remaining_vulns,
                chunks,
                len(commit_messages),
                self.notification_size_limit,
            )
        webhook_url = self.mr_webhook_url or self.general_webhook_url
        self._send_notification(webhook_url, chunks)

    def send_failure_notification(
        self,
        error_details: str,
        project: Optional[RemoteProject],
        context: str,
        dep_vuln_report: Optional[AuditReport] = None,
        logfile_url: Optional[str] = None,
    ) -> None:
        self.logger.debug(
            f"Sending failure notification for context: {context} Failed, "
            f"project: {project.name_with_namespace if project else ''}"
        )
        title = project.name_with_namespace if project else "Global Failure"
        subtitle = f"{context} Failed"
        project_url = project.web_url if project else None
        error_summary = f"An error occurred during: {context}"
        if len(error_details) > self.notification_size_limit:
            self.logger.error(
                f"Error details exceeded size limit of {self.notification_size_limit}. Truncating the details."
            )
            error_details = error_details[: self.notification_size_limit]
        if dep_vuln_report:
            error_summary += f": {dep_vuln_report.dep.name} with severity {dep_vuln_report.severity.name.lower()}"

        failure_notification_content = create_failure_notification_content(
            title, subtitle, project_url, error_summary, error_details, logfile_url
        )
        webhook_url = self.mr_webhook_url or self.general_webhook_url
        self._send_notification(webhook_url, [failure_notification_content])
