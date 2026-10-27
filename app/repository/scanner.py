from dataclasses import dataclass
import os
from pathlib import Path

from app.config import Config
from app.repository.detector import detect_language
from app.repository.security import is_sensitive_path


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
        if path.name in self.config.ignored_files or is_sensitive_path(path):
            return True

        try:
            return path.stat().st_size > self.config.max_file_size
        except OSError:
            # Files can disappear or become inaccessible during a scan. Skip
            # them instead of aborting discovery for the entire repository.
            return True

    def scan(self) -> list[FileInfo]:
        results: list[FileInfo] = []

        for directory, child_directories, filenames in os.walk(
            self.config.repository_root,
            topdown=True,
        ):
            child_directories[:] = [
                name for name in child_directories
                if name not in self.config.ignored_directories
                and not (Path(directory) / name).is_symlink()
            ]
            current_directory = Path(directory)
            for filename in filenames:
                path = current_directory / filename
                if path.is_symlink() or self.should_ignore_file(path):
                    continue

                language = detect_language(path)
                if language is None:
                    continue

                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    if "\x00" in content:
                        continue
                    relative_path = path.relative_to(self.config.repository_root)
                    results.append(FileInfo(
                        path=str(relative_path),
                        absolute_path=str(path),
                        language=language,
                        size=path.stat().st_size,
                        lines=len(content.splitlines()),
                    ))
                except (OSError, UnicodeError):
                    continue

        return sorted(results, key=lambda item: item.path.replace("\\", "/").casefold())
