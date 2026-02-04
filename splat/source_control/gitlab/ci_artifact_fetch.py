from typing import List, cast

from pydantic import ValidationError

from splat.interface.APIClient import JSON
from splat.interface.logger import LoggerInterface
from splat.source_control.gitlab.api import GitLabAPI
from splat.source_control.gitlab.model import GitLabPipelineBridge, GitLabPipelineJob
from splat.utils.env_manager.interface import EnvManager
from splat.utils.env_manager.os import OsEnvManager
from splat.utils.fs import FileSystemInterface, RealFileSystem
from splat.utils.logger_config import default_logger
from splat.utils.logging_utils import log_pydantic_validation_error


def fetch_downstream_pipeline_id(
    gitlab_api: GitLabAPI,
    project_endpoint: str,
    pipeline_id: str,
    logger: LoggerInterface = default_logger,
) -> str:
    logger.info("Fetching downstream pipeline ID...")
    endpoint = f"{project_endpoint}/pipelines/{pipeline_id}/bridges?per_page=100"
    bridges_json = cast(List[JSON], gitlab_api.get_json(endpoint))
    try:
        bridges = [GitLabPipelineBridge.model_validate(item) for item in bridges_json]
    except ValidationError as e:
        log_pydantic_validation_error(e, "Invalid GitLab pipeline bridges data", None, logger)  # None for now
        bridges = []
    for bridge in bridges:
        if bridge.downstream_pipeline:
            return str(bridge.downstream_pipeline.id)

    raise RuntimeError("Error: Could not retrieve downstream pipeline ID.")


def fetch_job_id(
    gitlab_api: GitLabAPI,
    project_endpoint: str,
    pipeline_id: str,
    job_name: str,
    logger: LoggerInterface = default_logger,
) -> str:
    logger.info(f"Fetching job ID for {job_name}...")
    page = 1
    per_page = 20  # keep default

    while True:
        params = {"per_page": str(per_page), "page": str(page)}
        endpoint = f"{project_endpoint}/pipelines/{pipeline_id}/jobs"
        jobs_json = cast(List[JSON], gitlab_api.get_json(endpoint, params))
        if not jobs_json:
            break

        try:
            jobs = [GitLabPipelineJob.model_validate(item) for item in jobs_json]
        except ValidationError as e:
            log_pydantic_validation_error(e, "Invalid GitLab jobs data", None)  # None for now
            jobs = []
        for job in jobs:
            if job.name == job_name:
                return str(job.id)
        page += 1

    raise RuntimeError(f"Error: Could not retrieve job ID for {job_name}.")


def download_artifact(
    gitlab_api: GitLabAPI,
    project_endpoint: str,
    job_id: str,
    fs: FileSystemInterface,
    logger: LoggerInterface = default_logger,
) -> None:
    logger.info("Downloading artifact dashboard/projects_summary.json...")
    endpoint = f"{project_endpoint}/jobs/{job_id}/artifacts/dashboard/projects_summary.json"
    artifact_byte = gitlab_api.get_bytes(endpoint)

    artifact_file = "projects_summary.json"
    fs.write(artifact_file, artifact_byte.decode())

    if not fs.exists(artifact_file):
        raise RuntimeError("Error: Failed to download artifact.")
    logger.info(f"Artifact downloaded: {artifact_file}")


def fetch_gitlab_ci_summary_artifact(access_token_name: str, env_manager: EnvManager | None = None) -> None:
    env_manager = env_manager or OsEnvManager(default_logger)
    ci_api_url = env_manager.get("CI_SERVER_URL")
    ci_project_id = env_manager.get("CI_PROJECT_ID")
    ci_pipeline_id = env_manager.get("CI_PIPELINE_ID")
    access_token = env_manager.get(access_token_name)

    api = GitLabAPI(api_url=ci_api_url, access_token=access_token)
    fs = RealFileSystem()
    project_endpoint = f"/projects/{ci_project_id}"

    downstream_pipeline_id = fetch_downstream_pipeline_id(api, project_endpoint, ci_pipeline_id)
    job_id = fetch_job_id(api, project_endpoint, downstream_pipeline_id, "aggregate_summaries")
    download_artifact(api, project_endpoint, job_id, fs)
