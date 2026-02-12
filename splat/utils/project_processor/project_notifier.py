from splat.interface.logger import LoggerInterface
from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from splat.model import AuditReport, MergeRequest, RemoteProject


class ProjectNotifier:
    def __init__(
        self,
        project: RemoteProject,
        notification_sinks: list[NotificationSinksInterface],
        logger: LoggerInterface,
    ) -> None:
        self.project = project
        self.notification_sinks = notification_sinks
        self.logger = logger

    def notify_failure(self, context: str, error: Exception, vulnerability: AuditReport | None = None) -> None:
        for sink in self.notification_sinks:
            self.logger.update_context(f"splat -> {self.project.name_with_namespace} -> {sink.type}")
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
            self.logger.update_context(f"splat -> {self.project.name_with_namespace} -> {sink.type}")
            sink.send_merge_request_notification(
                merge_request=mr,
                commit_messages=commit_messages,
                remaining_vulns=remaining_vulns,
            )

    def notify_project_skipped(self, reason: str, logfile_url: str | None = None) -> None:
        for sink in self.notification_sinks:
            self.logger.update_context(f"splat -> {self.project.name_with_namespace} -> {sink.type}")
            sink.send_project_skipped_notification(project=self.project, reason=reason, logfile_url=logfile_url)
