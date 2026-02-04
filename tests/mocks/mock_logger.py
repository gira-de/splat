from typing import List

from splat.config.model import LogLevel
from splat.interface.logger import LoggerInterface


class MockLogger(LoggerInterface):
    def __init__(self, context: str = "mock") -> None:
        self.context = context
        self.logged_messages: List[str] = []

    def info(self, msg: str) -> None:
        self.logged_messages.append(f"[{self.context}] INFO: {msg}")

    def debug(self, msg: str) -> None:
        self.logged_messages.append(f"[{self.context}] DEBUG: {msg}")

    def warning(self, msg: str) -> None:
        self.logged_messages.append(f"[{self.context}] WARNING: {msg}")

    def error(self, msg: str) -> None:
        self.logged_messages.append(f"[{self.context}] ERROR: {msg}")

    def update_context(self, new_context: str = "splat") -> None:
        self.context = new_context

    def update_log_level(self, log_level: LogLevel) -> None:
        self.logged_messages.append(f"[{self.context}] DEBUG: Log level updated to {log_level.value}")

    def has_logged(self, expected_msgs: str | list[str]) -> bool:
        if isinstance(expected_msgs, str):
            expected_msgs = [expected_msgs]
        return all(any(expected_msg in msg for msg in self.logged_messages) for expected_msg in expected_msgs)
