from typing import Optional, cast

from pydantic import ValidationError

from splat.config.model import PlatformConfig
from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.utils.logger_config import logger
from splat.utils.logging_utils import format_filters_log, log_pydantic_validation_error
from splat.utils.plugin_initializer.dynamic_import import get_class
from splat.utils.plugin_initializer.errors import SourceControlConfigError, SourceControlsConfigurationError

SOURCE_CONTROL_MODULE_PATH = "splat.source_control"


def get_git_platform_class(platform_type: str) -> type[GitPlatformInterface]:
    """
    Returns the git platform class for the given platform type.
    """
    class_name = f"{platform_type.capitalize()}Platform"
    module_path = f"{SOURCE_CONTROL_MODULE_PATH}.{platform_type}.{class_name}"
    cls = get_class(module_path, class_name)
    return cast(type[GitPlatformInterface], cls)


def initialize_git_platforms(
    platforms_configs: list[PlatformConfig], platform_id: Optional[str] = None
) -> list[GitPlatformInterface]:
    initiated_git_platforms: list[GitPlatformInterface] = []
    formatted_names: list[str] = []
    config_errors: list[SourceControlConfigError] = []

    # Filter platforms based on platform_id if provided
    if platform_id:
        filtered_configs = [p for p in platforms_configs if p.id == platform_id]

        if len(filtered_configs) == 0:
            raise ValueError(f"No Platform found with ID '{platform_id}'")
        if len(filtered_configs) > 1:
            raise ValueError(f"Multiple platforms found with ID '{platform_id}'. Please ensure IDs are unique.")

        platforms_configs = filtered_configs

    # Iterate over the (filtered or all) platform configurations
    for platform_config in platforms_configs:
        formatted_name = f"'{platform_config.type}': '{platform_config.name}'"
        try:
            platform_class = get_git_platform_class(platform_config.type)
            platform_instance = platform_class.from_platform_config(platform_config)
            initiated_git_platforms.append(platform_instance)
            formatted_names.append(formatted_name)
            filters_log = format_filters_log(platform_config.filters)
            logger.debug(f"Source control platform {formatted_name} configured successfully with {filters_log}.")
        except ValidationError as e:
            log_pydantic_validation_error(
                error=e,
                prefix_message=f"Validation error in platform configuration for {platform_config.type}",
                unparsable_data=None,
            )
            continue
        except Exception as e:
            logger.error(f"Error configuring source control platform: {formatted_name}: {e}")
            config_errors.append(SourceControlConfigError(platform=formatted_name, error=e))
            continue

    if len(initiated_git_platforms) == 0:
        raise SourceControlsConfigurationError(config_errors)
    logger.info(
        f"Configured {len(initiated_git_platforms)} source control platforms:"
        f"{', '.join(fn for fn in formatted_names)}"
    )
    return initiated_git_platforms
