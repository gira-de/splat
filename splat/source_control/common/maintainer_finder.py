from splat.interface.logger import LoggerInterface

TOPIC_PREFIXES = ("splat-maintainer:", "splat-maintainer-", "maintainer:", "maintainer-")


def parse_maintainer_from_topics(topics: list[str]) -> str | None:
    best_priority: int | None = None
    best_maintainer: str | None = None

    for raw_topic in topics:
        topic = (raw_topic or "").strip()
        if not topic:
            continue

        match = _extract_maintainer(topic)
        if match is not None:
            priority, maintainer = match
            if best_priority is None or priority < best_priority:
                best_priority = priority
                best_maintainer = maintainer
            if best_priority == 0:
                break

    return best_maintainer


def _extract_maintainer(topic: str) -> tuple[int, str] | None:
    for index, prefix in enumerate(TOPIC_PREFIXES):
        if topic[: len(prefix)].lower() == prefix:
            maintainer = topic[len(prefix) :].strip()
            if maintainer:
                return index, maintainer
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
