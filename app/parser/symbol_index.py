
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