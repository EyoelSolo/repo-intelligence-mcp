
from dataclasses import asdict, dataclass
from pathlib import Path

from app.parser.code_parser import CodeParser
from app.repository.scanner import RepositoryScanner


@dataclass
class SymbolDefinition:
    name: str
    kind: str
    file: str
    start_line: int
    end_line: int

class SymbolIndex:
    def __init__(
        self,
        scanner: RepositoryScanner,
        parser: CodeParser,
    ):
        self.scanner = scanner
        self.parser = parser
        self.definitions: list[SymbolDefinition] = []
        self.by_name: dict[str, list[SymbolDefinition]] = {}
        self.built = False