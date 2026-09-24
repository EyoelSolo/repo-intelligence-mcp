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

            relative_string = str(
                relative
            ).replace("\\", "/")

            if relative_string in file_index:
                return relative_string

        # Try directory imports:
        #
        # import "./services"
        #
        # could resolve to:
        #
        # services/index.ts
        index_files = [
            "index.ts",
            "index.tsx",
            "index.js",
            "index.jsx",
        ]

        for index_file in index_files:

            possible_file = candidate / index_file

            try:
                relative = possible_file.relative_to(
                    self.scanner.config.repository_root
                )

            except ValueError:
                continue

            relative_string = str(
                relative
            ).replace("\\", "/")

            if relative_string in file_index:
                return relative_string

        return None

    def get_dependencies(
        self,
        relative_path: str,
    ) -> list[str]:

        file_index = self.build_file_index()

        normalized_path = relative_path.replace(
            "\\",
            "/",
        )

        if normalized_path not in file_index:
            return []

        file_path = file_index[normalized_path]

        language = detect_language(file_path)

        if language is None:
            return []

        imports = self.parser.extract_imports(
            file_path,
            language,
        )
        dependencies = []

        for import_item in imports:

            resolved = self.resolve_import(
                file_path,
                import_item.source,
                file_index,
            )

            if resolved is not None:
                dependencies.append(resolved)

        return sorted(set(dependencies))