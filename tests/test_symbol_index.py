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
def test_indexes_function_and_class(tmp_path):
    (tmp_path / "service.ts").write_text(
        "class UserService {}\n"
        "function getUser() { return null; }\n",
        encoding="utf-8",
    )

    index = make_index(tmp_path)
    results = index.find("getUser")

    assert len(results) == 1
    assert results[0]["kind"] == "function"
    assert results[0]["file"] == "service.ts"
    assert results[0]["start_line"] == 2