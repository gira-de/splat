import json

from splat.interface.logger import LoggerInterface
from splat.utils.fs import FileSystemInterface, RealFileSystem
from splat.utils.logger_config import default_logger


class PackageJsonManager:
    def __init__(self, fs: FileSystemInterface = RealFileSystem(), logger: LoggerInterface = default_logger) -> None:
        self.fs = fs
        self.logger = logger

    def add_resolutions_block_to_package_json(
        self, package_json_path: str, dep_name: str, dep_fixed_version: str
    ) -> None:
        self.logger.debug(f"Adding resolution for {dep_name} to {dep_fixed_version} " f"in {package_json_path}")
        package_json_content = self.fs.read(package_json_path)
        package_json = json.loads(package_json_content)

        resolutions = package_json.get("resolutions", {})
        resolutions[dep_name] = f"^{dep_fixed_version}"
        package_json["resolutions"] = resolutions

        self.fs.write(package_json_path, json.dumps(package_json, indent=2))
