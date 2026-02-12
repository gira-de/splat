from __future__ import annotations

from pathlib import Path

from splat.utils.fs import FileSystemInterface


class MockFileSystem(FileSystemInterface):
    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.directories: set[str] = set()

    def read(self, file: str) -> str:
        if file not in self.files:
            raise FileNotFoundError(f"File {file} not found.")
        return self.files[file]

    def write(self, file: str, content: str) -> None:
        self.files[file] = content

    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> None:
        self.directories.add(path)

    def glob(self, path: str, pattern: str) -> list[str]:
        if pattern.startswith("**/"):
            suffix = pattern[3:]
            base_prefix = f"{path}/"
            if "/" in suffix:
                return [file for file in self.files if file.startswith(base_prefix) and file.endswith(suffix)]
            return [file for file in self.files if file.startswith(base_prefix) and Path(file).name == suffix]
        return [file for file in self.files if Path(file).match(f"{path}/{pattern}")]

    def exists(self, path: str) -> bool:
        return path in self.directories or path in self.files

    def home(self) -> Path:
        return Path("home")
