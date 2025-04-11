from typing import Any

from splat.model import Dependency, DependencyType


def extract_major_version(version: str) -> str:
    stripped_version = version.lstrip("=<>~")
    return stripped_version.split(".")[0]  # Get only the major version


def extract_deps_from_section(section: dict[str, Any], is_dev: bool) -> list[Dependency]:
    deps = []
    for dep_name, dep_value in section.items():
        if isinstance(dep_value, dict):
            version_str = dep_value.get("version", "")
        else:
            version_str = dep_value
        stripped_version = extract_major_version(version_str)
        deps.append(Dependency(name=dep_name, type=DependencyType.DIRECT, version=stripped_version, is_dev=is_dev))
    return deps
