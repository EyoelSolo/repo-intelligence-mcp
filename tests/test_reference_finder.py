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

def test_finds_function_definition_and_call(tmp_path):
    (tmp_path / "service.ts").write_text(
        "function getUser() { return null; }\n",
        encoding="utf-8",
    )
    (tmp_path / "controller.ts").write_text(
        "const user = getUser();\n",
        encoding="utf-8",
    )
    finder = make_finder(tmp_path)
    results = finder.find_references("getUser")

    assert len(results) == 2
    assert {item["kind"] for item in results} == {
        "definition",
        "call",
    }