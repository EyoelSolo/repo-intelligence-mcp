from pathlib import Path


LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".pyi": "python",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".vue": "vue",
    ".svelte": "svelte",
    ".json": "json",
    ".jsonc": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "configuration",
    ".conf": "configuration",
    ".properties": "properties",
    ".ipynb": "json",
    ".xml": "xml",
    ".md": "markdown",
    ".mdx": "markdown",
    ".rst": "restructuredtext",
    ".txt": "text",
    ".text": "text",
    ".log": "text",
    ".csv": "csv",
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
