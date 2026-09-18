from pathlib import Path

from app.repository.detector import (
    detect_language,
    is_javascript,
    is_typescript,
)

def test_javascript_detection():
    assert (
        detect_language(Path("app.js"))
        == "javascript"
    )

def test_jsx_detection():
    assert (
        detect_language(Path("App.jsx"))
        == "javascript"
    )


def test_typescript_detection():
    assert (
        detect_language(Path("app.ts"))
        == "typescript"
)

def test_javascript_helper():
    assert is_javascript(
        Path("server.js")
)
