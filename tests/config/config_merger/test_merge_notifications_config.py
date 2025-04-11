import unittest
from typing import cast
from unittest.mock import MagicMock, patch

from splat.config.config_merger import _merge_notifications_config
from splat.config.model import LocalNotificationSinksConfig, SinkConfig
from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from tests.mocks import MockLogger


class TestMergeNotificationsConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_logger = MockLogger()
        self.global_notification_sinks = [
            cast(NotificationSinksInterface, MagicMock(type="GlobalSink1")),
            cast(NotificationSinksInterface, MagicMock(type="GlobalSink2")),
        ]

    def test_merge_notifications_config_when_no_local_config_is_present(self) -> None:
        result_sinks = _merge_notifications_config(
            self.global_notification_sinks, LocalNotificationSinksConfig(), self.mock_logger
        )
        self.assertEqual(result_sinks, self.global_notification_sinks)
        self.assertTrue(self.mock_logger.has_logged("INFO: No notification was configured. Skipping notifications.."))

    @patch("splat.config.config_merger.initialize_notification_sinks")
    def test_merge_notifications_config_with_use_global_is_true_in_local_config(
        self, mock_initialize_sinks: MagicMock
    ) -> None:
        local_sink = cast(NotificationSinksInterface, MagicMock(type="LocalSink1"))
        mock_initialize_sinks.return_value = [local_sink]

        local_config = LocalNotificationSinksConfig(
            use_global_config=True,
            sinks=[SinkConfig(type="LocalSink1")],
        )

        result_sinks = _merge_notifications_config(self.global_notification_sinks, local_config, self.mock_logger)
        self.assertEqual(len(self.global_notification_sinks), 2)
        self.assertIsNotNone(result_sinks)
        if result_sinks is not None:
            self.assertEqual(len(result_sinks), 3)
            self.assertIn(local_sink, result_sinks)
            self.assertIn(self.global_notification_sinks[0], result_sinks)
            self.assertIn(self.global_notification_sinks[1], result_sinks)

    @patch("splat.config.config_merger.initialize_notification_sinks")
    def test_merge_notifications_config_when_use_global_is_false_in_local_config(
        self, mock_initialize_sinks: MagicMock
    ) -> None:
        local_sink = cast(NotificationSinksInterface, MagicMock(name="LocalSink1"))
        mock_initialize_sinks.return_value = [local_sink]

        local_config = LocalNotificationSinksConfig(
            use_global_config=False,
            sinks=[SinkConfig(type="LocalSink1")],
        )
        result_sinks = _merge_notifications_config(self.global_notification_sinks, local_config, self.mock_logger)
        self.assertEqual(len(self.global_notification_sinks), 2)
        self.assertIsNotNone(result_sinks)
        if result_sinks is not None:
            self.assertEqual(len(result_sinks), 1)
            self.assertIn(local_sink, result_sinks)
            self.assertNotIn(self.global_notification_sinks[0], result_sinks)
            self.assertNotIn(self.global_notification_sinks[1], result_sinks)

    @patch("splat.config.config_merger.initialize_notification_sinks")
    def test_merge_notifications_configs_when_no_local_sinks_and_use_global_is_true(
        self, mock_initialize_sinks: MagicMock
    ) -> None:
        mock_initialize_sinks.return_value = []

        local_config = LocalNotificationSinksConfig(use_global_config=True, sinks=[])

        result_sinks = _merge_notifications_config(self.global_notification_sinks, local_config, self.mock_logger)

        self.assertEqual(len(self.global_notification_sinks), 2)
        self.assertIsNotNone(result_sinks)
        if result_sinks is not None:
            self.assertEqual(len(result_sinks), 2)
            self.assertIn(self.global_notification_sinks[0], result_sinks)
            self.assertIn(self.global_notification_sinks[1], result_sinks)
            self.assertEqual(result_sinks, self.global_notification_sinks)

    @patch("splat.config.config_merger.initialize_notification_sinks")
    def test_merge_notifications_configs_when_no_local_sinks_and_use_global_is_false(
        self, mock_initialize_sinks: MagicMock
    ) -> None:
        mock_initialize_sinks.return_value = []

        local_config = LocalNotificationSinksConfig(use_global_config=False, sinks=[])

        result_sinks = _merge_notifications_config(self.global_notification_sinks, local_config, self.mock_logger)
        self.assertEqual(len(self.global_notification_sinks), 2)
        self.assertIsNotNone(result_sinks)
        if result_sinks is not None:
            self.assertEqual(len(result_sinks), 0)
            self.assertNotIn(self.global_notification_sinks[0], result_sinks)
            self.assertNotIn(self.global_notification_sinks[1], result_sinks)


if __name__ == "__main__":
    unittest.main()
