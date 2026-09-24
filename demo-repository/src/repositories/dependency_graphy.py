from pathlib import Path

from app.repository.detector import detect_language
from app.repository.scanner import RepositoryScanner
from app.parser.code_parser import CodeParser


class DependencyGraph:

    def __init__(
        self,
        scanner: RepositoryScanner,
        parser: CodeParser,
    ):
        self.scanner = scanner
        self.parser = parser