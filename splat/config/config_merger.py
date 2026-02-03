from splat.config.model import (
    Config,
    GeneralConfig,
    HooksConfig,
    LocalConfig,
    LocalGeneralConfig,
    LocalHooksConfig,
    LocalNotificationSinksConfig,
    LocalPackageManagersConfig,
    PMConfig,
)
from splat.interface.logger import LoggerInterface
from splat.interface.NotificationSinksInterface import NotificationSinksInterface
from splat.interface.PackageManagerInterface import PackageManagerInterface
from splat.utils.logger_config import default_logger
from splat.utils.logging_utils import log_general_config, log_hooks_config
from splat.utils.plugin_initializer.notification_init import initialize_notification_sinks
from splat.utils.plugin_initializer.package_managers_init import initialize_package_managers


def merge_configs(
    global_config: Config,
    local_config: LocalConfig,
    global_notification_sinks: list[NotificationSinksInterface],
    global_package_managers: list[PackageManagerInterface],
    logger: LoggerInterface | None = None,
) -> tuple[
    Config,
    list[NotificationSinksInterface],
    list[PackageManagerInterface],
]:
    logger = logger or default_logger
    merged_general_config = _merge_general_configs(global_config.general, local_config.general, logger)
    merged_hooks = _merge_hooks_config(global_config.hooks, local_config.hooks, logger)
    merged_notifications = _merge_notifications_config(global_notification_sinks, local_config.notifications, logger)
    merged_package_managers = _merge_package_managers_config(
        global_package_managers, local_config.package_managers, logger
    )
    return (
        Config(general=merged_general_config, hooks=merged_hooks),
        merged_notifications,
        merged_package_managers,
    )


def _merge_general_configs(
    global_general_config: GeneralConfig,
    local_general_config: LocalGeneralConfig | None,
    logger: LoggerInterface,
) -> GeneralConfig:
    merged_general_config = global_general_config.model_copy()
    changes_made = False

    if local_general_config:
        if local_general_config.logging is not None and local_general_config.logging != global_general_config.logging:
            logger.debug(
                "Project-specific configuration provided for 'logging'. Overriding global settings:\n"
                f"Global logging level: {global_general_config.logging.level.name} -> "
                f"Local logging level: {local_general_config.logging.level.name}"
            )
            merged_general_config.logging = merged_general_config.logging.model_copy(
                update=local_general_config.logging.model_dump(exclude_unset=True)
            )
            changes_made = True
        if local_general_config.debug is not None and local_general_config.debug != global_general_config.debug:
            logger.debug(
                "Project-specific configuration provided for 'debug'. Overriding global settings:\n"
                f"Global debug 'skip_cleanup': {global_general_config.debug.skip_cleanup} -> "
                f"Local debug 'skip_cleanup': {local_general_config.debug.skip_cleanup}"
            )
            merged_general_config.debug = merged_general_config.debug.model_copy(
                update=local_general_config.debug.model_dump(exclude_unset=True)
            )
            changes_made = True
    if changes_made is False:
        logger.debug(
            "No overrides were provided by the project-specific general config. "
            "Continuing with the global general configuration."
        )

    log_general_config(merged_general_config, logger)
    return merged_general_config


def _merge_notifications_config(
    global_notification_sinks: list[NotificationSinksInterface],
    local_notifications_config: LocalNotificationSinksConfig | None,
    logger: LoggerInterface,
) -> list[NotificationSinksInterface]:
    merged_notifications_sinks = global_notification_sinks.copy()

    if local_notifications_config is None:
        logger.debug("No project-specific notification configuration provided. Using global configuration only.")
    else:
        local_sinks = initialize_notification_sinks(local_notifications_config, logger)

        if local_notifications_config.use_global_config is False:
            logger.debug("Using project-specific notification configuration only. Global configuration is ignored.")
            return local_sinks

        merged_notifications_sinks += local_sinks
        logger.debug(
            f"Adding {len(local_sinks)} local notification sinks to the "
            f"existing {len(global_notification_sinks)} global sinks"
        )

    return merged_notifications_sinks


def _merge_hooks_config(
    global_hooks_config: HooksConfig,
    local_hooks_config: LocalHooksConfig | None,
    logger: LoggerInterface,
) -> HooksConfig:
    if global_hooks_config is None and local_hooks_config is None:
        logger.debug("No hooks configuration provided. Skipping hooks...")
        return

    if local_hooks_config is None:
        logger.debug("No project-specific hooks configuration provided. Using global hooks configuration.")
        return global_hooks_config

    if global_hooks_config is None:
        merged_hooks = local_hooks_config.pre_commit.copy()
        logger.debug("Using project-specific hooks configuration only, No global hooks configuration provided.")
    elif local_hooks_config.use_global_config:
        merged_hooks = global_hooks_config.pre_commit.copy()
        for pattern, local_script_config in local_hooks_config.pre_commit.items():
            # Local overrides global if the pattern exists in both
            merged_hooks[pattern] = local_script_config
            logger.info(f"Project-specific hook for pattern '{pattern}' overrides the global hook.")
    else:
        merged_hooks = local_hooks_config.pre_commit.copy()
        logger.debug("Using project-specific hooks configuration only. Ignoring global hooks.")

    merged_hooks_config = HooksConfig(pre_commit=merged_hooks)
    log_hooks_config(merged_hooks_config, logger)

    return merged_hooks_config


def _merge_package_managers_config(
    global_package_managers: list[PackageManagerInterface],
    local_package_managers_config: LocalPackageManagersConfig | None,
    logger: LoggerInterface,
) -> list[PackageManagerInterface]:
    if local_package_managers_config is None:
        logger.debug("No project-specific package manager configuration provided. Using global configuration.")
        return global_package_managers

    global_pm_names = {pm.name.lower() for pm in global_package_managers}
    final_package_managers = global_package_managers[:]
    unspecified_pms = []

    for local_pm_name in local_package_managers_config.model_fields:
        local_pm_config: PMConfig | None = getattr(local_package_managers_config, local_pm_name)
        if local_pm_config is None:
            unspecified_pms.append(local_pm_name)
            continue

        if local_pm_config.enabled is True:
            if local_pm_name not in global_pm_names:
                # New package manager: initialize and add it.
                pm_class = initialize_package_managers(
                    LocalPackageManagersConfig(**{local_pm_name: local_pm_config}), logger
                )
                final_package_managers.append(pm_class[0])
                global_pm_names.add(local_pm_name)
                logger.debug(f"Enabled project-specific package manager '{local_pm_name}'.")
            else:
                # Existing PM: merge repository configurations (local overrides global).
                for pm in final_package_managers:
                    if pm.name.lower() == local_pm_name:
                        merged_repos = {**pm.config.repositories, **local_pm_config.repositories}
                        pm.config.repositories = merged_repos
                        logger.debug(f"Merged repositories for project-specific package manager '{local_pm_name}'.")
                        break
        else:  # disable this package manager.
            if local_pm_name in global_pm_names:
                final_package_managers = [pm for pm in final_package_managers if pm.name.lower() != local_pm_name]
                global_pm_names.discard(local_pm_name)
                logger.debug(f"Disabled project-specific package manager '{local_pm_name}'.")
            else:
                logger.debug(f"Project-specific package manager '{local_pm_name}' is already disabled.")

    if unspecified_pms:
        logger.debug(
            f"Package manager(s) '{', '.join(unspecified_pms)}' are not specified in the project-specific "
            "configuration. Keeping global configuration."
        )

    return final_package_managers
