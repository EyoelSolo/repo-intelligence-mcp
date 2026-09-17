from dataclasses import dataclass
from pathlib import path


@dataclass
class Config: 
    repository_root: path


    ignored_directories: tuple [str, ...] = (
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".next",
        ".nuxt",
        ".venv",
        "venv",
        "__pycache__",
    )

    ignored_files:tuple[str, ...] = (
        ".env",
        ".env.local",
        ".env.production",
        ".env.developenent",
        ".env.test",
        "id_rsa",
        "id_ed25519",
    )
    max_file_size: int = 1_000_000