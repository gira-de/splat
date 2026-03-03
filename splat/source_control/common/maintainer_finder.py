from splat.interface.logger import LoggerInterface

TOPIC_PREFIXES = ("splat-maintainer:", "splat-maintainer-", "maintainer:", "maintainer-")


def parse_maintainer_from_topics(topics: list[str]) -> str | None:
    for maintainer_prefix in TOPIC_PREFIXES:
        for topic in topics:
            if topic[0 : len(maintainer_prefix)].lower() == maintainer_prefix:
                maintainer = topic[len(maintainer_prefix) :]
                if len(maintainer) > 0:
                    return maintainer

    return None


def find_project_maintainer(project_name: str, topics: list[str], logger: LoggerInterface) -> str | None:
    if not topics:
        logger.debug(f"No project topics found for {project_name}")
        return None

    maintainer = parse_maintainer_from_topics(topics)
    if maintainer is None:
        logger.debug(f"No maintainer topic found for {project_name}")
        return None

    logger.info(f"Found matching project topic for {project_name}: {maintainer}")
    return maintainer
