from typing import Optional

import toml

from splat.interface.logger import LoggerInterface
from splat.model import Dependency
from splat.package_managers.common.dependency_utils import extract_deps_from_section
from splat.utils.fs import FileSystemInterface, RealFileSystem
from splat.utils.logger_config import default_logger


class PoetryPyprojectManager:
    def __init__(self, fs: FileSystemInterface = RealFileSystem(), logger: LoggerInterface = default_logger) -> None:
        self.fs = fs
        self.logger = logger

    def get_required_python_version(self, pyproject_path: str) -> Optional[str]:
        try:
            pyproject_content = toml.loads(self.fs.read(pyproject_path))
        except Exception as e:
            self.logger.error(f"Error reading {pyproject_path}: {e}")
            return None

        python_version = pyproject_content.get("tool", {}).get("poetry", {}).get("dependencies", {}).get("python", None)
        if python_version is None:
            self.logger.error(f"Python version not specified in {pyproject_path}")
            return None
        clean_version = python_version.lstrip("^~>=<").strip()
        return f"python{clean_version}"

    def get_direct_deps(self, pyproject_path: str) -> list[Dependency]:
        """
        Extracts all the direct dependencies from a pyproject.toml (used by Poetry)
        and indicates whether they are dev dependencies."""
        pyproject_content = toml.loads(self.fs.read(pyproject_path))
        deps: list[Dependency] = []
        poetry_tool = pyproject_content.get("tool", {}).get("poetry", {})
        dependencies = poetry_tool.get("dependencies", {})
        dependencies.pop("python", None)
        deps.extend(extract_deps_from_section(dependencies, is_dev=False))
        deps.extend(
            extract_deps_from_section(poetry_tool.get("group", {}).get("dev", {}).get("dependencies", {}), is_dev=True)
        )
        return deps

    def get_sources(self, pyproject_path: str) -> dict[str, str]:
        """
        Parse the given pyproject.toml file to extract Poetry source (repositories) definitions.
        Returns a dictionary mapping repository names to their URLs.
        """
        pyproject_content = toml.loads(self.fs.read(pyproject_path))
        # Navigate to the sources under [tool.poetry.source]
        sources = pyproject_content.get("tool", {}).get("poetry", {}).get("source", [])
        if not isinstance(sources, list):
            sources = [sources]

        repo_configs = {source["name"]: source["url"] for source in sources if "name" in source and "url" in source}

        return repo_configs
