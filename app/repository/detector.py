from pathlib import Path


LANGUAGE_EXTENSIONS = {
    ".js": "javascript", 
    ".jsx": "javascript",
     ".mjs": "javascript",
    ".cjs": "javascript",

    ".ts": "typescript",
    ".tsx": "tsx",
    ".mts": "typescript",
    ".cts": "typescript",

}

def detect_language(path: Path) -> str | None: 
    return LANGUAGE_EXTENSIONS.get(path.suffix.lower())

def is_javascript(path: Path) -> bool: 
    return detect_language(path) == "javascript"

def is_typescript(path: Path) -> bool: 
    return detect_language(path) in {"typescript", "tsx"}

def is_supported_code_file(path:Path) -> bool:
    return detect_language(path) is not None
