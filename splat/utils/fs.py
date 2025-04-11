from abc import ABC, abstractmethod
from pathlib import Path


class FileSystemInterface(ABC):
    @abstractmethod
    def read(self, file: str) -> str:
        pass

    def write(self, file: str, content: str) -> None:
        pass

    @abstractmethod
    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> None:
        pass

    @abstractmethod
    def glob(self, path: str, pattern: str) -> list[str]:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def home(self) -> Path:
        pass


class RealFileSystem(FileSystemInterface):
    def read(self, file: str) -> str:
        with open(file, "r") as f:
            return f.read()

    def write(self, file: str, content: str) -> None:
        with open(file, "w") as f:
            f.write(content)

    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> None:
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def glob(self, path: str, pattern: str) -> list[str]:
        return [str(p) for p in Path(path).glob(pattern)]

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def home(self) -> Path:
        return Path.home()
