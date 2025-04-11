from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from splat.config.model import SinkConfig
from splat.model import AuditReport, MergeRequest, RemoteProject


class NotificationSinksInterface(ABC):
    def __init__(self, config: SinkConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def from_sink_config(cls, sink_config: SinkConfig) -> NotificationSinksInterface:
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
        project: Optional[RemoteProject],
        context: str,
        dep_vuln_report: Optional[AuditReport] = None,
        logfile_url: Optional[str] = None,
    ) -> None:
        pass
