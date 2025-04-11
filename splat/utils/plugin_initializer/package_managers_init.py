from typing import Optional, cast

from splat.config.model import LocalPackageManagersConfig, PackageManagersConfig
from splat.interface.logger import LoggerInterface
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.utils.logger_config import default_logger
from splat.utils.logging_utils import log_configured_package_managers
from splat.utils.plugin_initializer.dynamic_import import get_class
from splat.utils.plugin_initializer.errors import PackageManagersConfigurationError

PACKAGE_MANAGERS_MODULE_PATH = "splat.package_managers"


def get_pm_class(pm_name: str) -> type[PackageManagerInterface]:
    class_name = f"{pm_name.capitalize()}PackageManager"
    module = f"{PACKAGE_MANAGERS_MODULE_PATH}.{pm_name.lower()}.{class_name}"
    cls = get_class(module, class_name)
    return cast(type[PackageManagerInterface], cls)


def initialize_package_managers(
    package_managers_config: PackageManagersConfig | LocalPackageManagersConfig,
    logger: Optional[LoggerInterface] = None,
) -> list[PackageManagerInterface]:
    logger = logger or default_logger
    initiated_package_managers: list[PackageManagerInterface] = []
    configured_pms: dict[str, bool] = {}
    try:
        pm_names = PackageManagersConfig.model_fields.keys()

        for pm_name in pm_names:
            pm_class = get_pm_class(pm_name)
            pm_config = getattr(package_managers_config, pm_name, None)

            if pm_config is not None:
                if pm_config.enabled is True:
                    pm_instance = pm_class(pm_config)
                    initiated_package_managers.append(pm_instance)
                    configured_pms[pm_name] = True
                    logger.debug(f"Package manager '{pm_name}' configured successfully: enabled")
                else:
                    configured_pms[pm_name] = False
                    logger.debug(f"Package manager '{pm_name}' configured successfully: disabled")
    except Exception as e:
        raise PackageManagersConfigurationError(e)

    if configured_pms:
        log_configured_package_managers(configured_pms, logger)
    return initiated_package_managers
