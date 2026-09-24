from pathlib import Path

from app.repository.detector import detect_language
from app.repository.scanner import RepositoryScanner
from app.parser.code_parser import CodeParser


class DependencyGraph:

    def __init__(
        self,
        scanner: RepositoryScanner,
        parser: CodeParser,
    ):
        self.scanner = scanner
        self.parser = parser

    def build_file_index(self) -> dict[str, Path]:
        """
        Create an index from repository-relative paths
        to absolute paths.
        """

        index = {}

        for file in self.scanner.scan():
            index[file.path.replace("\\", "/")] = Path(
                file.absolute_path
            )

        return index
    def resolve_import(
        self,
        importing_file: Path,
        import_source: str,
        file_index: dict[str, Path],
    ) -> str | None:
        """
        Resolve a relative JavaScript/TypeScript import
        to a repository-relative file.
        """

        # Ignore external packages such as:
        #
        # react
        # express
        # axios
        #
        if not import_source.startswith("."):
            return None
        base_directory = importing_file.parent

        candidate = (
            base_directory / import_source
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