import yaml
from pydantic import BaseModel, Field

from splat.environments.common import fetch_filtered_projects_for_platforms
from splat.interface.ExecutionEnvironmentInterface import ExecutionEnvironmentInterface
from splat.interface.logger import LoggerInterface
from splat.model import RemoteProject


class DockerConfig(BaseModel):
    user: str


class ImageConfig(BaseModel):
    name: str
    pull_policy: str
    docker: DockerConfig


class Artifacts(BaseModel):
    paths: list[str]


class Rule(BaseModel):
    when: str


class Job(BaseModel):
    script: list[str]
    needs: list[str] | None = Field(default=None)
    artifacts: Artifacts | None = Field(default=None)
    rules: list[Rule] | None = Field(default=None)


class Default(BaseModel):
    image: ImageConfig


class Pipeline(BaseModel, extra="allow"):
    __pydantic_extra__: dict[str, Job] = Field(init=False)

    default: Default
    aggregate_summaries: Job | None


def _generate_pipeline(platform_to_projects: dict[str, list[RemoteProject]], logger: LoggerInterface) -> Pipeline:
    logger.debug("Generating child pipeline YAML in GitLab CI Environment...")
    jobs: dict[str, Job] = {}
    process_job_names = []
    default_rules = [Rule(when="on_success")]

    for platform_id, projects in platform_to_projects.items():
        for project in projects:
            job_name = f"process_{project.name_with_namespace}"
            process_job_names.append(job_name)
            script = [f"splat --platform-id {platform_id} --project-id {project.id}"]
            rules = default_rules
            # Add artifacts to the process jobs
            artifacts = Artifacts(paths=["dashboard/"])
            # Add the job to the dictionary
            jobs[job_name] = Job(script=script, rules=rules, artifacts=artifacts)

    # Add an aggregation job only if there are process jobs
    if process_job_names:
        aggregate_job_script = [
            "python3 /splat/aggregate_summaries.py --input-dir dashboard "
            + "--output-file dashboard/projects_summary.json"
        ]
        aggregate_job = Job(
            script=aggregate_job_script,
            needs=process_job_names,
            artifacts=Artifacts(paths=["dashboard/projects_summary.json"]),
            rules=default_rules,
        )
    else:
        aggregate_job = None
    default = Default(
        image=ImageConfig(name="${DEFAULT_SPLAT_IMAGE}", pull_policy="always", docker=DockerConfig(user="splatuser"))
    )
    result = Pipeline(default=default, aggregate_summaries=aggregate_job)
    for job_id, job in jobs.items():
        setattr(result, job_id, job)
    return result


# GitLab CI Environment Implementation
class GitLabCIEnvironment(ExecutionEnvironmentInterface):
    def execute(self) -> None:
        """Fetch projects and generate downstream pipelines."""
        self.logger.info("Executing in GitLab environment...")

        platform_to_projects = fetch_filtered_projects_for_platforms(self.git_platforms, self.logger)
        pipeline = _generate_pipeline(platform_to_projects, self.logger)

        # Write the pipeline to a YAML file
        yaml_file_path = "child-pipeline.yml"
        content = yaml.dump(
            pipeline.model_dump(exclude_none=True), sort_keys=False, indent=2, default_flow_style=False, width=1000
        )
        self.ctx.fs.write(yaml_file_path, content)
