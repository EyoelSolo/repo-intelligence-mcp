from pathlib import Path

from app.config import Config
from app.parser.code_parser import CodeParser
from app.parser.reference_finder import ReferenceFinder
from app.repository.scanner import RepositoryScanner


def make_finder(root: Path) -> ReferenceFinder:
    config = Config(root)
    return ReferenceFinder(
        scanner=RepositoryScanner(config),
        parser=CodeParser(),
    )