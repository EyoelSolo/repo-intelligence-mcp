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