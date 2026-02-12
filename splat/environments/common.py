from splat.interface.GitPlatformInterface import GitPlatformInterface
from splat.interface.logger import LoggerInterface
from splat.model import RemoteProject
from splat.utils.project_processor.project_filter import filter_projects


def fetch_filtered_projects_for_platforms(
    git_platforms: list[GitPlatformInterface], logger: LoggerInterface
) -> dict[str, list[RemoteProject]]:
    platform_to_projects: dict[str, list[RemoteProject]] = {}

    for platform in git_platforms:
        logger.update_context(platform.type)
        if not platform.id:
            logger.error(f"Platform ID missing for platform: {platform.type}. Skipping..")
            continue
        projects = platform.fetch_projects()
        projects = filter_projects(projects, platform.config.filters, logger)
        platform_to_projects[platform.id] = projects

    if len(platform_to_projects.items()) == 0:
        raise ValueError("No source control platform was configured with an ID.")

    return platform_to_projects
