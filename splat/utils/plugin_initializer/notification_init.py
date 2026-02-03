from collections import defaultdict
from typing import cast

from splat.config.model import NotificationSinksConfig
from splat.interface.logger import LoggerInterface
from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from splat.utils.logger_config import default_logger
from splat.utils.plugin_initializer.dynamic_import import get_class

NOTIFICATIONS_MODULE_PATH = "splat.notifications"


def get_notification_sink_class(sink_type: str) -> type[NotificationSinksInterface]:
    """
    Returns the notification sink class for the given sink type.
    """
    class_name = f"{sink_type.capitalize()}NotificationSink"
    module_path = f"{NOTIFICATIONS_MODULE_PATH}.{sink_type}.{class_name}"
    cls = get_class(module_path, class_name)
    return cast(type[NotificationSinksInterface], cls)


def initialize_notification_sinks(
    notification_sinks_configs: NotificationSinksConfig, logger: LoggerInterface | None = None
) -> list[NotificationSinksInterface]:
    """
    Initializes and returns a list of notification sink instances based on the provided configuration.
    """
    logger = logger or default_logger
    initiated_notification_sinks: list[NotificationSinksInterface] = []
    formatted_names: list[str] = []
    sink_counts: defaultdict[str, int] = defaultdict(int)

    for sink_config in notification_sinks_configs.sinks:
        formatted_name = f"'{sink_config.type}': '{sink_config.name}'"
        try:
            sink_class = get_notification_sink_class(sink_config.type)
            sink_instance = sink_class.from_sink_config(sink_config)
            initiated_notification_sinks.append(sink_instance)
            formatted_names.append(formatted_name)
            sink_counts[sink_config.type] += 1
            logger.debug(f"Notification sink {formatted_name} configured successfully.")
        except Exception as e:
            logger.error(f"Error configuring notification sink: {formatted_name}: {e}")
            continue

    if len(initiated_notification_sinks) == 0:
        logger.info("No notification was configured. Skipping notifications..")
    else:
        for sink_type, count in sink_counts.items():
            logger.debug(f"Configured {count} sinks of type '{sink_type}'")
        logger.info(
            f"Configured {len(initiated_notification_sinks)} notification sinks: "
            f"{', '.join(fn for fn in formatted_names)}"
        )
    return initiated_notification_sinks
