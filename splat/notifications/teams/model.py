from pydantic import BaseModel, Field

from splat.config.model import SinkConfig


class TeamsPayloadContentBodyElementAction(BaseModel):
    type: str
    title: str
    target_elements: list[dict[str, str]] = Field(alias="targetElements")


class TeamsPayloadContentBodyElement(BaseModel):
    type: str
    text: str | None = None
    weight: str | None = None
    size: str | None = None
    color: str | None = None
    wrap: bool | None = None
    id: str | None = None
    is_visible: bool | None = Field(default=None, alias="isVisible")
    actions: list[TeamsPayloadContentBodyElementAction] | None = None


class MSTeams(BaseModel):
    width: str


class TeamsPayloadContent(BaseModel):
    msteams: MSTeams
    schema_: str = Field(serialization_alias="$schema")
    type: str
    version: str
    body: list[TeamsPayloadContentBodyElement]


class TeamsPayloadAttachment(BaseModel):
    content_type: str = Field(alias="contentType")
    content: TeamsPayloadContent


class TeamsPayload(BaseModel):
    type: str
    attachments: list[TeamsPayloadAttachment]


#  config
class MergeRequestSinkConfig(BaseModel):
    webhook_url: str


class UpdateFailureSinkConfig(BaseModel):
    webhook_url: str


class ProjectSkippedSinkConfig(BaseModel):
    webhook_url: str


class ErrorSinkConfig(BaseModel):
    webhook_url: str


class TeamsSinkConfig(SinkConfig):
    webhook_url: str
    merge_request: MergeRequestSinkConfig | None = None
    update_failure: UpdateFailureSinkConfig | None = None
    project_skipped: ProjectSkippedSinkConfig | None = None
    error: ErrorSinkConfig | None = None
