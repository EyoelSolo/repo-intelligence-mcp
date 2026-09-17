from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_javascript
import tree_sitter_typescript


@dataclass
class Symbol:
    name: str
    kind: str
    file: str
    start_line: int
    end_line: int


@dataclass
class Import:
    source: str
    file: str
    start_line: int


class CodeParser:

    def __init__(self):
        self.javascript_language = Language(
            tree_sitter_javascript.language()
        )

        self.typescript_language = Language(
            tree_sitter_typescript.language_typescript()
        )

        self.tsx_language = Language(
            tree_sitter_typescript.language_tsx())

        def get_parser(self, language: str) -> Parser:

            if language == "javascript":
                return Parser(self.javascript_language)

            if language == "typescript":
                return Parser(self.typescript_language)

            if language == "tsx":
                return Parser(self.tsx_language)

            raise ValueError(f"Unsupported language: {language}")

        def parse_file(
            self,
            path: Path,
            language: str,
        ):
            parser = self.get_parser(language)

            source = path.read_bytes()

            return parser.parse(source)