from __future__ import annotations

from abc import ABC, abstractmethod

from splat.config.model import SinkConfig
from splat.interface.logger import LoggerInterface
from splat.model import AuditReport, MergeRequest, RemoteProject
from splat.utils.env_manager.interface import EnvManager


class NotificationSinksInterface(ABC):
    def __init__(self, config: SinkConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def from_sink_config(
        cls, sink_config: SinkConfig, logger: LoggerInterface, env_manager: EnvManager
    ) -> NotificationSinksInterface:
        pass

    @abstractmethod
    def send_merge_request_notification(
        self, merge_request: MergeRequest, commit_messages: list[str], remaining_vulns: list[AuditReport]
    ) -> None:
        pass

    @abstractmethod
    def send_failure_notification(
        self,
        error_details: str,
        project: RemoteProject | None,
        context: str,
        dep_vuln_report: AuditReport | None = None,
        logfile_url: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    def send_project_skipped_notification(
        self, project: RemoteProject, reason: str, logfile_url: str | None = None
    ) -> None:
        """
        Notify that the project processing was skipped/aborted for a given reason (e.g. manual changes on the branch).
        """
        pass
