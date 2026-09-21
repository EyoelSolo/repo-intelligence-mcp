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

def test_tsx_detection():
    assert detect_language(Path("App.tsx")) == "tsx"

def test_mjs_detection():
    assert detect_language(Path("app.mjs")) == "javascript"

def test_cjs_detection():
    assert detect_language(Path("app.cjs")) == "javascript"

def test_mts_detection():
    assert detect_language(Path("app.mts")) == "typescript"

def test_cts_detection():
    assert detect_language(Path("app.cts")) == "typescript"

def test_javascript_helper():
    assert is_javascript(
        Path("server.js")
)

def test_typescript_helper():
    assert is_typescript(
        Path("server.ts")
    )



def test_unknown_language():
    assert (
        detect_language(Path("main.py"))
        is None
    )