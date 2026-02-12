from datetime import datetime
from pathlib import Path

from splat.config.model import Config
from splat.environments.GithubActionsEnvironment import GitHubActionsEnvironment
from splat.environments.GitlabCIEnvironment import GitLabCIEnvironment
from splat.environments.LocalEnvironment import LocalEnvironment
from splat.model import RuntimeContext
from splat.utils.parseargs import SplatArgs
from splat.utils.plugin_initializer.notification_init import initialize_notification_sinks
from splat.utils.plugin_initializer.package_managers_init import initialize_package_managers
from splat.utils.plugin_initializer.source_control_init import initialize_git_platforms
from splat.utils.project_processor.project_operations import export_json_summary
from splat.utils.project_processor.single_project import clone_and_process_project


def process_remote_projects(args: SplatArgs, config: Config, ctx: RuntimeContext) -> None:
    git_platforms = initialize_git_platforms(
        config.source_control.platforms,
        logger=ctx.logger,
        env_manager=ctx.env_manager,
        platform_id=args.platform_id,
    )
    environment = (
        GitHubActionsEnvironment(config, git_platforms, ctx)
        if ctx.env_manager.get_optional("GITHUB_ACTIONS") == "true"
        else GitLabCIEnvironment(config, git_platforms, ctx)
        if ctx.env_manager.get_optional("GITLAB_CI") == "true"
        else LocalEnvironment(config, git_platforms, ctx)
    )
    environment.execute()


def process_project_with_id(args: SplatArgs, config: Config, ctx: RuntimeContext) -> None:
    if args.platform_id is None or args.project_id is None:
        raise ValueError(
            "Missing required arguments. Ensure the following arguments are provided: " "--platform-id, --project-id."
        )
    git_platforms = initialize_git_platforms(
        config.source_control.platforms,
        logger=ctx.logger,
        env_manager=ctx.env_manager,
        platform_id=args.platform_id,
    )
    git_platform = git_platforms[0]
    package_managers = initialize_package_managers(config.package_managers, ctx)
    notification_sinks = initialize_notification_sinks(
        config.notifications, logger=ctx.logger, env_manager=ctx.env_manager
    )

    projects = git_platform.fetch_projects(args.project_id)
    p_summary = clone_and_process_project(
        projects[0], package_managers, git_platform, notification_sinks, config, ctx=ctx
    )
    if p_summary:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_json_path = Path(f"dashboard/{args.project_id}_summary_{timestamp}.json")
        export_json_summary([p_summary], json_path=unique_json_path, logger=ctx.logger, fs=ctx.fs)
