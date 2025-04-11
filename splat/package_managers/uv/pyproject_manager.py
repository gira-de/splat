import re

import toml

from splat.model import Dependency, DependencyType
from splat.utils.fs import FileSystemInterface, RealFileSystem


class UvPyprojectManager:
    def __init__(self, fs: FileSystemInterface = RealFileSystem()) -> None:
        self.fs = fs

    def get_direct_deps(self, pyproject_path: str) -> list[Dependency]:
        """
        Extracts all the direct dependencies from a pyproject.toml (used by uv)
        and indicates whether they are dev dependencies."""
        pyproject_content = toml.loads(self.fs.read(pyproject_path))

        deps: list[Dependency] = []

        # Regular expression to capture the package name before the version specifier
        version_regex = re.compile(r"([^\s>=<~!]+)")

        # Extract regular dependencies from 'project.dependencies'
        for dep in pyproject_content.get("project", {}).get("dependencies", []):
            match = version_regex.match(dep)
            if match:
                package_name = match.group(1)
                deps.append(Dependency(name=package_name, type=DependencyType.DIRECT, is_dev=False))

        # Extract dev dependencies from 'tool.uv.dev-dependencies'
        for dep in pyproject_content.get("tool", {}).get("uv", {}).get("dev-dependencies", []):
            match = version_regex.match(dep)
            if match:
                package_name = match.group(1)
            deps.append(Dependency(name=package_name, type=DependencyType.DIRECT, is_dev=True))

        return deps

    def get_indexes(self, pyproject_path: str) -> dict[str, str]:
        pyproject_content = toml.loads(self.fs.read(pyproject_path))
        uv_indexes = pyproject_content.get("tool", {}).get("uv", {}).get("index", [])
        if not isinstance(uv_indexes, list):
            uv_indexes = [uv_indexes]

        repo_configs = {}
        for index in uv_indexes:
            if "name" in index and "url" in index:
                repo_configs[index["name"]] = index["url"]
        return repo_configs
