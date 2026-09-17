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

    def __post_init__(self):
        self.repository_root = self.repository_root.resolve()

        if not self.repository_root.exists():
            raise ValueError(
                f"Repository does not exist: {self.repository_root}"
            )
        if not self.repository_root.is_dir():
            raise ValueError(
                f"repository path is not a directory: {self.repository_root}"
            )