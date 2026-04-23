from pydantic import BaseModel

from splat.config.model import PlatformConfig


class GitLabConfig(PlatformConfig):
    domain: str
    access_token: str


class GitLabRepositoryEntry(BaseModel, extra="allow"):
    id: int
    path_with_namespace: str
    name: str
    http_url_to_repo: str
    web_url: str
    default_branch: str | None


class GitLabMergeRequestEntry(BaseModel, extra="allow"):
    id: int
    iid: int
    title: str
    description: str
    state: str
    source_branch: str
    web_url: str


class GitLabProjectTopicsEntry(BaseModel, extra="allow"):
    topics: list[str]


class GitLabUserEntry(BaseModel, extra="allow"):
    id: int


class GitLabDownstreamPipeline(BaseModel, extra="allow"):
    id: str | int


class GitLabPipelineBridge(BaseModel, extra="allow"):
    downstream_pipeline: GitLabDownstreamPipeline | None


class GitLabMergeRequestPutEntry(BaseModel, extra="allow"):
    assignee_id: int | None


class GitLabPipelineJob(BaseModel, extra="allow"):
    id: str | int
    name: str
