import re
from typing import Optional

from splat.config.model import FiltersConfig
from splat.model import RemoteProject
from splat.utils.logger_config import logger


def filter_projects(projects: list[RemoteProject], filters: Optional[FiltersConfig]) -> list[RemoteProject]:
    included_projects = projects
    excluded_projects = []

    logger.debug("All accessible projects: \n" + ", ".join(project.name_with_namespace for project in projects))
    if filters is None:
        return projects

    if len(filters.include) > 0:
        try:
            logger.debug(f"Include patterns: {filters.include}")
            include_patterns = [re.compile(pattern) for pattern in filters.include]
            included_projects = [
                project
                for project in projects
                if any(pattern.match(project.name_with_namespace) for pattern in include_patterns)
            ]
            logger.debug(
                "Included Projects: \n" + ", ".join(project.name_with_namespace for project in included_projects)
            )
        except re.error as e:
            raise re.error(f"Invalid include filter patterns: {e}")

    if len(filters.exclude) > 0:
        try:
            logger.debug(f"Exclude patterns: {filters.exclude}")
            exclude_patterns = [re.compile(pattern) for pattern in filters.exclude]
            excluded_projects = [
                project
                for project in projects
                if any(pattern.match(project.name_with_namespace) for pattern in exclude_patterns)
            ]
            logger.debug(
                "Excluded Projects: \n" + ", ".join(project.name_with_namespace for project in excluded_projects)
            )
        except re.error as e:
            raise re.error(f"Invalid exclude filter patterns: {e}")

    excluded_project_names = {project.name_with_namespace for project in excluded_projects}
    filtered_projects = [
        project for project in included_projects if project.name_with_namespace not in excluded_project_names
    ]
    logger.info(
        "Filtered projects that will be cloned and processed are:"
        f"\n{', '.join(fp.name_with_namespace for fp in filtered_projects)}"
    )

    return filtered_projects
