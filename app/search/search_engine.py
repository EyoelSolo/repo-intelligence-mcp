from pathlib import Path

from app.config import Config
from app.repository.scanner import RepositoryScanner

MAX_RESULT_CONTENT_CHARS = 1000


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

    def search(
        self,
        query: str,
        limit: int = 20,
        case_sensitive: bool = False,
    ) -> list[dict]:

        if limit <= 0 or not query:
            return []

        needle = query if case_sensitive else query.casefold()

        results = []

        files = self.scanner.scan()

        for file_info in files:

            path = Path(file_info.absolute_path)

            try:
                lines = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).splitlines()

            except OSError:
                continue

            for line_number, line in enumerate(
                lines,
                start=1,
            ):

                haystack = line if case_sensitive else line.casefold()
                if needle in haystack:
                    content = line.strip()
                    if len(content) > MAX_RESULT_CONTENT_CHARS:
                        content = content[:MAX_RESULT_CONTENT_CHARS - 3] + "..."

                    result = SearchResult(
                        file=file_info.path,
                        line=line_number,
                        content=content,
                    )

                    results.append(result.to_dict())

                    if len(results) >= limit:
                        return results

        return results
