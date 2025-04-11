import toml
import tomlkit
from tomlkit.items import InlineTable, Table

from splat.interface.logger import LoggerInterface
from splat.model import Dependency
from splat.package_managers.common.dependency_utils import extract_deps_from_section
from splat.utils.fs import FileSystemInterface


class PipfileManager:
    def __init__(self, fs: FileSystemInterface, logger: LoggerInterface) -> None:
        self.fs = fs
        self.logger = logger

    def get_direct_deps(self, pipfile_path: str) -> list[Dependency]:
        """Reads a Pipfile from a file path and extracts all direct dependencies with their version
        from a Pipfile content and indicates whether they are dev dependencies."""
        pipfile_content = toml.loads(self.fs.read(pipfile_path))
        deps: list[Dependency] = []
        deps.extend(extract_deps_from_section(pipfile_content.get("packages", {}), is_dev=False))
        deps.extend(extract_deps_from_section(pipfile_content.get("dev-packages", {}), is_dev=True))
        return deps

    def set_parent_deps_to_latest_minor_version(self, pipfile_path: str, parent_deps: list[Dependency]) -> None:
        """Updates the Pipfile to set parent dependencies to the latest minor version."""
        pipfile_content = toml.loads(self.fs.read(pipfile_path))

        packages = pipfile_content.get("packages", {})
        dev_packages = pipfile_content.get("dev-packages", {})

        for parent_dep in parent_deps:
            if parent_dep.version is None:
                raise RuntimeError(f"Failed to set Direct Dependency {parent_dep.name} to latest Minor Version")

            if parent_dep.name in packages:
                packages[parent_dep.name] = f"~={parent_dep.version}.0"
            elif parent_dep.name in dev_packages:
                dev_packages[parent_dep.name] = f"~={parent_dep.version}.0"

        self.fs.write(pipfile_path, toml.dumps(pipfile_content))

    def sync_pipfile_with_installed_versions(self, pipfile_path: str, requirements: str) -> None:
        """
        Sync the Pipfile with exact versions from pip freeze output.

        Args:
            pipfile_path (str): Path to the Pipfile.
            requirements (str): Output of `pip freeze`, containing `package==version` pairs.

        Updates the `[packages]` and `[dev-packages]` sections of the Pipfile
        to match the exact versions installed.
        """
        self.logger.debug(f"Updating {pipfile_path} with exact installed versions...")

        pipfile_doc = tomlkit.parse(self.fs.read(pipfile_path))
        packages = pipfile_doc.get("packages", tomlkit.table())
        dev_packages = pipfile_doc.get("dev-packages", tomlkit.table())

        requirements_dict = self._parse_requirements(requirements)

        for section_name, package_dict in {"packages": packages, "dev-packages": dev_packages}.items():
            self._update_package_versions(section_name, package_dict, requirements_dict)

        self.fs.write(pipfile_path, tomlkit.dumps(pipfile_doc))

    def _parse_requirements(self, requirements: str) -> dict[str, str]:
        """
        Parse requirements from pip freeze output.

        Args:
            requirements (str): Output of `pip freeze`.

        Returns:
            dict: A mapping of normalized package names to versions.
        """
        requirements_dict = {}
        for line in requirements.splitlines():
            if "==" in line:
                package, version = line.split("==")
                normalized_package = self._normalize_package_name(package)
                requirements_dict[normalized_package] = version.strip()
        return requirements_dict

    def _normalize_package_name(self, package: str) -> str:
        return package.strip().replace("_", "-").lower()

    def _update_package_versions(
        self, section_name: str, package_dict: Table, requirements_dict: dict[str, str]
    ) -> None:
        """
        Update package versions in a Pipfile section.

        Args:
            section_name (str): The section name (e.g., 'packages', 'dev-packages').
            package_dict (tomlkit.items.Table): The TOML table to update.
            requirements_dict (dict): Mapping of package names to exact versions.
        """
        log_packages = []
        for package in list(package_dict.keys()):
            normalized_package = self._normalize_package_name(package)
            if normalized_package in requirements_dict:
                exact_version = f"=={requirements_dict[normalized_package]}"
                log_packages.append(f"Syncing {package} to {exact_version}")
                self._update_package_entry(package_dict, package, exact_version)

        if log_packages:
            self.logger.debug(f"Updated {section_name}: " + ", ".join(log_packages))

    def _update_package_entry(self, package_dict: Table, package: str, exact_version: str) -> None:
        """
        Update a single package entry in the Pipfile.

        Args:
            package_dict (tomlkit.items.Table): The TOML table containing the package.
            package (str): The package name.
            exact_version (str): The exact version to set.
        """
        current_value = package_dict[package]
        if isinstance(current_value, InlineTable):
            # Rebuild inline table to preserve key order
            new_inline = tomlkit.inline_table()
            for key, value in current_value.items():
                new_inline.add(key, exact_version if key == "version" else value)
            package_dict[package] = new_inline
        else:
            package_dict[package] = exact_version

    def get_sources(self, pipfile_path: str) -> dict[str, str]:
        """
        Parse the given Pipfile to extract Pipenv source (repository) definitions.
        Returns a dictionary mapping repository names to their URLs.
        """
        try:
            pipfile_content = toml.loads(self.fs.read(pipfile_path))
        except Exception as e:
            raise Exception(f"Failed to load {pipfile_path}: {e}")

        # Pipenv's Pipfile defines sources at the top level as a list of tables.
        sources = pipfile_content.get("source", [])
        if not isinstance(sources, list):
            sources = [sources]

        repo_configs = {source["name"]: source["url"] for source in sources if "name" in source and "url" in source}
        return repo_configs
