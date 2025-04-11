from typing import Optional

from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.utils.logger_config import logger


class ProjectNotifier:
    def __init__(self, project: RemoteProject, notification_sinks: list[NotificationSinksInterface]) -> None:
        self.project = project
        self.notification_sinks = notification_sinks

    def notify_failure(self, context: str, error: Exception, vulnerability: Optional[AuditReport] = None) -> None:
        for sink in self.notification_sinks:
            logger.update_context(f"splat -> {self.project.name_with_namespace} -> {sink.type}")
            sink.send_failure_notification(
                error_details=str(error),
                project=self.project,
                context=context,
                dep_vuln_report=vulnerability,
            )

    def notify_mr_success(
        self, mr: MergeRequest, commit_messages: list[str], remaining_vulns: list[AuditReport]
    ) -> None:
        for sink in self.notification_sinks:
            logger.update_context(f"splat -> {self.project.name_with_namespace} -> {sink.type}")
            sink.send_merge_request_notification(
                merge_request=mr,
                commit_messages=commit_messages,
                remaining_vulns=remaining_vulns,
            )
