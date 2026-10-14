from pathlib import Path

from app.config import Config
from app.parser.code_parser import CodeParser
from app.parser.symbol_index import SymbolIndex
from app.repository.scanner import RepositoryScanner


def make_index(root: Path) -> SymbolIndex:
    return SymbolIndex(
        scanner=RepositoryScanner(Config(root)),
        parser=CodeParser(),
    )