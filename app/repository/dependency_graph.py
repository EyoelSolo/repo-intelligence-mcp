from dataclasses import dataclass
from pathlib import Path

from app.parser.code_parser import CodeParser
from app.repository.detector import detect_language
from app.repository.scanner import RepositoryScanner


@dataclass
class DependencyGraph:
    scanner: RepositoryScanner
    parser: CodeParser

    def __post_init__(self):
        self.file_index: dict[str, Path] = {}
        self.dependencies: dict[str, set[str]] = {}
        self.dependents: dict[str, set[str]] = {}
    def build_file_index(self) -> None:
        """
        Build a mapping between repository-relative paths
        and absolute filesystem paths.
        """

        self.file_index.clear()

        for file in self.scanner.scan():
            relative_path = file.path.replace("\\", "/")

            self.file_index[relative_path] = Path(
                file.absolute_path
            )
    def resolve_import(
        self,
        importing_file: Path,
        import_source: str,
    ) -> str | None:
        """
        Resolve a local JavaScript/TypeScript import
        to a repository-relative path.
        """

        # External packages:
        #
        # react
        # express
        # axios
        #
        # are not repository dependencies.

        if not import_source.startswith("."):
            return None

        candidate = (
            importing_file.parent / import_source
        ).resolve()

        extensions = [
            "",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".mts",
            ".cts",
            ".mjs",
            ".cjs",
        ]
         for extension in extensions:

            possible_file = Path(
                str(candidate) + extension
            )

            try:
                relative = possible_file.relative_to(
                    self.scanner.config.repository_root
                )
            except ValueError:
                continue

            relative_path = str(relative).replace(
                "\\",
                "/",
            )

            if relative_path in self.file_index:
                return relative_path