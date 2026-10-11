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

def test_ignores_comments_and_strings(tmp_path):
    (tmp_path / "example.ts").write_text(
        '// getUser is mentioned here\n'
        'const message = "getUser";\n'
        'getUser();\n',
        encoding="utf-8",
    )
    results = make_finder(tmp_path).find_references("getUser")

    assert len(results) == 1
    assert results[0]["kind"] == "call"
    assert results[0]["line"] == 3

def test_returns_relative_path_and_line(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "app.ts").write_text(
        "\ngetUser();\n",
        encoding="utf-8",
    )

    results = make_finder(tmp_path).find_references("getUser")
    assert len(results) == 1
    assert results[0]["file"] == "src/app.ts"
    assert results[0]["line"] == 2