from typing import Optional

from pydantic import BaseModel

from splat.config.model import PlatformConfig


class GitLabConfig(PlatformConfig):
    domain: str
    access_token: str


class GitLabRepositoryEntry(BaseModel, extra="allow"):
    id: int
    path_with_namespace: str
    http_url_to_repo: str
    web_url: str
    default_branch: Optional[str]


class GitLabMergeRequestEntry(BaseModel, extra="allow"):
    id: int
    iid: int
    title: str
    description: str
    state: str
    source_branch: str
    web_url: str


class GitLabDownstreamPipeline(BaseModel, extra="allow"):
    id: str | int


class GitLabPipelineBridge(BaseModel, extra="allow"):
    downstream_pipeline: Optional[GitLabDownstreamPipeline]


class GitLabPipelineJob(BaseModel, extra="allow"):
    id: str | int
    name: str
