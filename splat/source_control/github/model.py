from pydantic import BaseModel

from splat.config.model import PlatformConfig


class GithubRepositoryEntry(BaseModel, extra="allow"):
    id: int
    full_name: str
    clone_url: str
    html_url: str
    default_branch: str


class RepoHeadGithubPullRequestEntry(BaseModel, extra="allow"):
    html_url: str


class HeadGithubPullRequestEntry(BaseModel, extra="allow"):
    repo: RepoHeadGithubPullRequestEntry


class GithubPullRequestEntry(BaseModel, extra="allow"):
    title: str
    body: str | None
    url: str
    html_url: str
    head: HeadGithubPullRequestEntry


class GitHubConfig(PlatformConfig):
    domain: str
    access_token: str
