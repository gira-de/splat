from splat.config.model import SinkConfig
from splat.interface.logger import LoggerInterface
from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.utils.env_manager.interface import EnvManager


class MockNotificationSink(NotificationSinksInterface):
    def __init__(self) -> None:
        self.merge_request_notifications: list[tuple[MergeRequest, list[str], list[AuditReport]]] = []
        self.project_skipped_notifications: list[tuple[RemoteProject, str, str | None]] = []
        self.failure_notifications: list[tuple[str, RemoteProject | None, str, AuditReport | None, str | None]] = []

    @property
    def type(self) -> str:
        return "recording"

    @classmethod
    def from_sink_config(
        cls, sink_config: SinkConfig, logger: LoggerInterface, env_manager: EnvManager
    ) -> NotificationSinksInterface:
        return cls()

    def send_merge_request_notification(
        self, merge_request: MergeRequest, commit_messages: list[str], remaining_vulns: list[AuditReport]
    ) -> None:
        self.merge_request_notifications.append((merge_request, commit_messages, remaining_vulns))

    def send_failure_notification(
        self,
        error_details: str,
        project: RemoteProject | None,
        context: str,
        dep_vuln_report: AuditReport | None = None,
        logfile_url: str | None = None,
    ) -> None:
        self.failure_notifications.append((error_details, project, context, dep_vuln_report, logfile_url))

    def send_project_skipped_notification(
        self, project: RemoteProject, reason: str, logfile_url: str | None = None
    ) -> None:
        self.project_skipped_notifications.append((project, reason, logfile_url))
