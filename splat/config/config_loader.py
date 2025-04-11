from pathlib import Path
from typing import Optional, cast

import yaml
from pydantic import ValidationError

from splat.config.model import Config, LocalConfig
from splat.interface.logger import LoggerInterface
from splat.utils.fs import FileSystemInterface, RealFileSystem
from splat.utils.logger_config import default_logger, logger, logger_manager
from splat.utils.logging_utils import log_general_config, log_hooks_config, log_pydantic_validation_error


def load_yaml_file(file_path: Path, fs: FileSystemInterface, raise_on_error: bool = True) -> dict[str, str]:
    try:
        content = fs.read(str(file_path))
        yaml_content = yaml.safe_load(content)
        return yaml_content if isinstance(yaml_content, dict) else {}
    except FileNotFoundError as e:
        if raise_on_error is True:
            raise e
        logger.info(f"Configuration file {file_path} not found. Using default settings.")
        return {}
    except yaml.YAMLError as e:
        if raise_on_error:
            raise e
        logger.error(f"Error parsing YAML configuration file {file_path}. Using default settings.")
        return {}


def validate_config(
    config_entry: dict[str, str],
    config_model: type[Config | LocalConfig],
    logger: LoggerInterface,
    raise_on_error: bool = True,
) -> Config | LocalConfig | None:
    try:
        return config_model.model_validate(config_entry)
    except ValidationError as e:
        log_pydantic_validation_error(e, "Configuration validation failed", config_entry, logger)
        if raise_on_error:
            raise RuntimeError(
                "Configuration validation error. Please check the configuration file and correct the issues above."
            ) from e
        return None


def load_config(
    config_path: Path = Path("splat.yaml"),
    logger: Optional[LoggerInterface] = None,
    fs: Optional[FileSystemInterface] = None,
) -> Config:
    logger = logger or default_logger
    fs = fs or RealFileSystem()
    config_path = config_path.resolve()
    logger.info(f"Loading global configuration from {config_path}")
    config_entry = load_yaml_file(config_path, fs, raise_on_error=True)
    config = validate_config(config_entry, Config, logger, raise_on_error=True)
    config = cast(Config, config)
    logger_manager.update_logger_level(config.general.logging.level)
    logger.debug("Global configuration loaded and validated successfully.")
    log_general_config(config.general, logger)
    log_hooks_config(config.hooks, logger)
    return config


def load_project_config(
    config_path: Path,
    logger: Optional[LoggerInterface] = None,
    fs: Optional[FileSystemInterface] = None,
) -> LocalConfig | None:
    logger = logger or default_logger
    fs = fs or RealFileSystem()

    if not fs.exists(str(config_path)):
        logger.info(f"Project specific configuration file {config_path} not found. Using default settings.")
        return None

    logger.info(f"Loading Project specific configuration from {config_path}")
    config_entry = load_yaml_file(config_path, fs, raise_on_error=False)

    if config_entry is None or config_entry == {}:
        logger.error(f"Project-specific configuration file {config_path} is empty or invalid. Using default settings.")
        return None

    config = validate_config(config_entry, LocalConfig, logger, raise_on_error=False)
    if config is not None:
        config = cast(LocalConfig, config)

    logger.debug("Project-specific configuration loaded and validated successfully.")

    return config
