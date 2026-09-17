from pathlib import Path

from app.config import Config
from app.repository.scanner import RepositoryScanner


class SearchResult:
    def __init__(
        self,
        file: str,
        line: int,
        content: str,
    ):
        self.file = file
        self.line = line
        self.content = content

    def to_dict(self):
        return {
            "file": self.file,
            "line": self.line,
            "content": self.content,
        }

    
class SearchEngine:

    def __init__(self, config: Config):
        self.config = config
        self.scanner = RepositoryScanner(config)