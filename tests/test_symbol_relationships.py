
from pathlib import Path

from app.config import Config
from app.parser.code_parser import CodeParser
from app.parser.reference_finder import ReferenceFinder
from app.parser.symbol_index import SymbolIndex
from app.parser.symbol_relationships import SymbolRelationships
from app.repository.scanner import RepositoryScanner



def test_combines_definitions_and_reference_candidates(
    tmp_path: Path,
):
    (tmp_path / "service.ts").write_text(
        "function getUser() { return null; }\n",
        encoding="utf-8",
    )
    (tmp_path / "controller.ts").write_text(
        "const user = getUser();\n",
        encoding="utf-8",
    )