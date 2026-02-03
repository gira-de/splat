import argparse
from pathlib import Path

from pydantic import BaseModel, Field


class SplatArgs(BaseModel):
    local_projects: list[Path] | None = Field(default=None)
    platform_id: str | None = Field(default=None)
    project_id: str | None = Field(default=None)
    gitlab_ci_fetch_summary: bool | None = Field(default=False)
    access_token_name: str | None = Field(default=None)


def parse_arguments() -> SplatArgs:
    parser = argparse.ArgumentParser(prog="Splat")
    parser.add_argument("--project", help="Process a local project folder instead of downloading projects", nargs="+")
    parser.add_argument(
        "--platform-id", help="Unique identifier for the source control platform in the configuration.", type=str
    )
    parser.add_argument(
        "--project-id", help="ID of the project to be processed from the source control system", type=str
    )
    parser.add_argument("--gitlab-ci-fetch-summary", help="Fetch GitLab CI projects summary", action="store_true")
    parser.add_argument(
        "--access-token", type=str, help="The environment variable name that stores the GitLab access token"
    )
    args = parser.parse_args()
    local_projects = [Path(project) for project in args.project] if args.project is not None else None
    return SplatArgs(
        local_projects=local_projects,
        platform_id=args.platform_id,
        project_id=args.project_id,
        gitlab_ci_fetch_summary=args.gitlab_ci_fetch_summary,
        access_token_name=args.access_token,
    )
