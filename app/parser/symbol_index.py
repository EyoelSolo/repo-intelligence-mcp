
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

    def build(self) -> None:
        definitions: list[SymbolDefinition] = []

        for file_info in self.scanner.scan():
            file_path = Path(file_info.absolute_path)

            try:
                symbols = self.parser.extract_symbols(
                    file_path,
                    file_info.language,
                )
            except (OSError, ValueError, UnicodeError):
                continue
            except Exception:
                # One unsupported or malformed file should not
                # prevent indexing the rest of the repository.
                continue
