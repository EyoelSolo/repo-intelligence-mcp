from dataclasses import dataclass
from pathlib import Path

from app.config import Config
from app.repository.detector import detect_language


@dataclass
class FileInfo:
    path: str
    absolute_path: str
    language: str | None
    size: int
    lines: int


class RepositoryScanner:

    def __init__(self, config: Config):
        self.config = config

    def should_ignore_directory(self, path: Path) -> bool:
        return path.name in self.config.ignored_directories

    def should_ignore_file(self, path: Path) -> bool:
        return (
            path.name in self.config.ignored_files
            or path.stat().st_size > self.config.max_file_size
        )

    def scan(self) -> list[FileInfo]:
        results: list[FileInfo] = []

        for path in self.config.repository_root.rglob("*"):

            if not path.is_file():
                continue

            if any(
                self.should_ignore_directory(parent)
                for parent in path.parents
                if parent != self.config.repository_root
            ):
                continue

            if self.should_ignore_file(path):
                continue

            language = detect_language(path)

            if language is None:
                continue

            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )

                relative_path = path.relative_to(
                    self.config.repository_root
                )

                results.append(
                    FileInfo(
                        path=str(relative_path),
                        absolute_path=str(path),
                        language=language,
                        size=path.stat().st_size,
                        lines=len(content.splitlines()),
                    )
                )

            except (OSError, UnicodeError):
                continue

        return results