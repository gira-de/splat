import unittest
from unittest.mock import MagicMock, patch

from splat.config.model import NotificationSinksConfig, SinkConfig
from splat.interface.NotificationSinksInterface import (
    NotificationSinksInterface,
)
from splat.utils.plugin_initializer.notification_init import (
    get_notification_sink_class,
    initialize_notification_sinks,
)
from tests.mocks import MockLogger


class TestNotificationInitializer(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_logger = MockLogger()

    @patch("splat.utils.plugin_initializer.notification_init.get_class")
    def test_get_notification_sink_class_valid_type(self, mock_get_class: MagicMock) -> None:
        mock_class = MagicMock(spec=NotificationSinksInterface)
        mock_get_class.return_value = mock_class

        sink_type = "email"
        sink_class = get_notification_sink_class(sink_type)

        mock_get_class.assert_called_once_with(
            "splat.notifications.email.EmailNotificationSink", "EmailNotificationSink"
        )
        self.assertEqual(sink_class, mock_class)

    @patch("splat.utils.plugin_initializer.notification_init.get_class")
    def test_get_notification_sink_class_invalid_type_raises_error(self, mock_get_class: MagicMock) -> None:
        mock_get_class.side_effect = ImportError("Invalid sink type")

        sink_type = "invalid_sink"

        with self.assertRaises(ImportError):
            get_notification_sink_class(sink_type)

        mock_get_class.assert_called_once_with(
            "splat.notifications.invalid_sink.Invalid_sinkNotificationSink",
            "Invalid_sinkNotificationSink",
        )

    @patch("splat.utils.plugin_initializer.notification_init.get_notification_sink_class")
    def test_initialize_notification_sinks_with_empty_configs(self, _: MagicMock) -> None:
        # Test with empty sinks list
        empty_config = NotificationSinksConfig(sinks=[])
        sinks = initialize_notification_sinks(empty_config, self.mock_logger)
        self.assertEqual(sinks, [])
        self.assertTrue(self.mock_logger.has_logged("No notification was configured. Skipping notifications.."))

    @patch("splat.utils.plugin_initializer.notification_init.get_notification_sink_class")
    def test_initialize_notification_sinks_logs_correct_information(
        self, mock_get_notification_sink_class: MagicMock
    ) -> None:
        # Setup a valid sink config
        mock_sink_class = MagicMock(spec=NotificationSinksInterface)
        mock_get_notification_sink_class.return_value = mock_sink_class
        mock_sink_instance = MagicMock(spec=NotificationSinksInterface)
        mock_sink_class.from_sink_config.return_value = mock_sink_instance

        valid_config = NotificationSinksConfig(sinks=[SinkConfig(type="email")])
        sinks = initialize_notification_sinks(valid_config, self.mock_logger)

        self.assertEqual(len(sinks), 1)
        expected_calls = [
            "DEBUG: Notification sink 'email': '' configured successfully.",
            "DEBUG: Configured 1 sinks of type 'email'",
            "INFO: Configured 1 notification sinks: 'email': ''",
        ]
        self.assertTrue(self.mock_logger.has_logged(expected_calls))

    @patch("splat.utils.plugin_initializer.notification_init.get_notification_sink_class")
    def test_initialize_notification_sinks_handles_exceptions(
        self, mock_get_notification_sink_class: MagicMock
    ) -> None:
        # Setup the get_notification_sink_class to raise an exception
        mock_get_notification_sink_class.side_effect = Exception("Test Exception")

        config_with_error = NotificationSinksConfig(sinks=[SinkConfig(type="invalid_type")])
        sinks = initialize_notification_sinks(config_with_error, self.mock_logger)

        self.assertEqual(sinks, [])
        self.assertTrue(
            self.mock_logger.has_logged(
                [
                    "Error configuring notification sink: 'invalid_type': '': Test Exception",
                    "No notification was configured. Skipping notifications..",
                ]
            )
        )


if __name__ == "__main__":
    unittest.main()
