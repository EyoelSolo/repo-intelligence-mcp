from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class Config: 
    repository_root: Path


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
        ".env.development",
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


    @classmethod
    def from_environment(cls) -> "Config":
        """Load the repository root from REPO_INTELLIGENCE_ROOT, if set."""
        configured_root = os.environ.get("REPO_INTELLIGENCE_ROOT")
        if configured_root:
            return cls(Path(configured_root))
        return cls(Path(__file__).resolve().parent.parent / "demo-repository")
