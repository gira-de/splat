from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class BaseModelWithNoneReplacement(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def not_none(cls, v: Any, validation_info: ValidationInfo) -> Any:
        if validation_info.field_name is not None:
            field = cls.model_fields[validation_info.field_name]
            if v is None:
                return field.get_default(call_default_factory=True)
            return v


class LogLevel(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LoggingConfig(BaseModel):
    level: LogLevel = Field(default=LogLevel.INFO)


class GitConfig(BaseModel):
    clone_dir: str = Field(
        default="/splat/splat_repos/",
        description="Base directory for cloned repositories",
    )
    branch_name: str = Field(default="splat")


class DebugConfig(BaseModel):
    skip_cleanup: bool = Field(default=False, description="Skip cleanup after processing")


class GeneralConfig(BaseModelWithNoneReplacement):
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    debug: DebugConfig = Field(default_factory=DebugConfig)


class FiltersConfig(BaseModel):
    exclude: list[str] = Field(
        default_factory=list,
        description="List of regex patterns to exclude repositories",
    )
    include: list[str] = Field(
        default_factory=list,
        description="List of regex patterns to include repositories",
    )


class PlatformConfig(BaseModelWithNoneReplacement, extra="allow"):
    type: str
    id: Optional[str] = Field(default=None)
    name: str = Field(default_factory=str)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)


class PlatformsConfig(BaseModelWithNoneReplacement):
    platforms: list[PlatformConfig] = Field(default_factory=list)


class SinkConfig(BaseModelWithNoneReplacement, extra="allow"):
    type: str
    name: str = Field(default_factory=str)


class NotificationSinksConfig(BaseModelWithNoneReplacement):
    sinks: list[SinkConfig] = Field(default_factory=list)


class RepoCredentials(BaseModel):
    username: Optional[str] = Field(None)
    password: Optional[str] = Field(None)
    token: Optional[str] = Field(None)


class RepoConfig(BaseModel):
    url: str
    credentials: Optional[RepoCredentials] = Field(None)


class PMConfig(BaseModelWithNoneReplacement):
    enabled: bool = Field(
        default=True,
        description="Whether updates are enabled for this package manager",
    )
    repositories: dict[str, RepoConfig] = Field(default_factory=dict)


class PackageManagersConfig(BaseModelWithNoneReplacement):
    pipenv: PMConfig = Field(default_factory=PMConfig)
    yarn: PMConfig = Field(default_factory=PMConfig)
    poetry: PMConfig = Field(default_factory=PMConfig)
    uv: PMConfig = Field(default_factory=PMConfig)


class HooksPreCommitConfig(BaseModelWithNoneReplacement):
    script: list[str] = Field(default_factory=list)
    cwd: str = Field(default="${SPLAT_PACKAGE_ROOT}")
    one_command_per_file: bool = Field(default=False)


class HooksConfig(BaseModel):
    pre_commit: dict[str, HooksPreCommitConfig] = Field(default_factory=dict)


class Config(BaseModelWithNoneReplacement):
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    source_control: PlatformsConfig = Field(default_factory=PlatformsConfig)
    notifications: NotificationSinksConfig = Field(default_factory=NotificationSinksConfig)
    hooks: HooksConfig = Field(default_factory=HooksConfig)
    package_managers: PackageManagersConfig = Field(default_factory=PackageManagersConfig)


class LocalGeneralConfig(BaseModel):
    logging: LoggingConfig | None = Field(default=None)
    debug: DebugConfig | None = Field(default=None)


class LocalNotificationSinksConfig(NotificationSinksConfig):
    use_global_config: bool = Field(default=True)


class LocalHooksConfig(HooksConfig):
    use_global_config: bool = Field(default=True)


class LocalPackageManagersConfig(BaseModel):
    pipenv: PMConfig | None = Field(default=None)
    yarn: PMConfig | None = Field(default=None)
    poetry: PMConfig | None = Field(default=None)
    uv: PMConfig | None = Field(default=None)


class LocalConfig(BaseModelWithNoneReplacement):
    general: LocalGeneralConfig | None = Field(default=None)
    notifications: LocalNotificationSinksConfig | None = Field(default=None)
    hooks: LocalHooksConfig | None = Field(default=None)
    package_managers: LocalPackageManagersConfig | None = Field(default=None)
