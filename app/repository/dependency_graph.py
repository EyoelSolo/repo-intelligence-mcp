from dataclasses import dataclass
from pathlib import Path

from app.parser.code_parser import CodeParser
from app.repository.detector import detect_language
from app.repository.scanner import RepositoryScanner


@dataclass
class DependencyGraph:
    scanner: RepositoryScanner
    parser: CodeParser

    def __post_init__(self):
        self.file_index: dict[str, Path] = {}
        self.dependencies: dict[str, set[str]] = {}
        self.dependents: dict[str, set[str]] = {}