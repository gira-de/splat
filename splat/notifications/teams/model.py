from typing import Optional

from pydantic import BaseModel, Field

from splat.config.model import SinkConfig


class TeamsPayloadContentBodyElementAction(BaseModel):
    type: str
    title: str
    target_elements: list[dict[str, str]] = Field(alias="targetElements")


class TeamsPayloadContentBodyElement(BaseModel):
    type: str
    text: Optional[str] = None
    weight: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    wrap: Optional[bool] = None
    id: Optional[str] = None
    is_visible: Optional[bool] = Field(default=None, alias="isVisible")
    actions: Optional[list[TeamsPayloadContentBodyElementAction]] = None


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


class ErrorSinkConfig(BaseModel):
    webhook_url: str


class TeamsSinkConfig(SinkConfig):
    webhook_url: str
    merge_request: Optional[MergeRequestSinkConfig] = None
    update_failure: Optional[UpdateFailureSinkConfig] = None
    error: Optional[ErrorSinkConfig] = None
