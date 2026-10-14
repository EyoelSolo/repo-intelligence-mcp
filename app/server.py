import logging

from pathlib import Path
from app.parser import reference_finder
from app.repository.dependency_graph import DependencyGraph

from mcp.server.mcpserver import MCPServer
from app.repository.impact_analyzer import ImpactAnalyzer

from app.config import Config
from app.parser.code_parser import CodeParser
from app.repository.scanner import RepositoryScanner
from app.repository.security import safe_path, SecurityError
from app.search.search_engine import SearchEngine
from app.repository.detector import detect_language
from app.parser.symbol_index import SymbolIndex
from app.parser.symbol_relationships import SymbolRelationships



logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


#configuration
REPOSITORY_PATH = Path(
   
    "./demo-repository"
)

config = Config(REPOSITORY_PATH)

scanner = RepositoryScanner(config)
parser = CodeParser()
symbol_index = SymbolIndex(scanner, parser)
symbol_index.build()
search_engine = SearchEngine(config)
reference_finder = reference_finder(config)
dependency_graph = DependencyGraph(
    scanner,
    parser,
)
dependency_graph.build()

#mcp server
mcp = MCPServer(
    "Repository Intelligence"
)

symbol_relationships = SymbolRelationships(
    symbol_index=symbol_index,
    reference_finder=reference_finder,
)
impact_analyzer = ImpactAnalyzer(
    dependency_graph
)
#repository information

@mcp.tool()
def repository_info() -> dict:
    """
    Return basic information about the repository.
    """

    files = scanner.scan()

    languages = {}

    for file in files:
        languages[file.language] = (
            languages.get(file.language, 0) + 1
        )

    return {
        "repository": str(config.repository_root),
        "total_supported_files": len(files),
        "languages": languages,
    }
@mcp.tool()
def get_dependencies(
    path: str,
) -> list[str]:
    """
    Return local repository files imported by a file.
    """

    try:
        safe_path(
            config.repository_root,
            path,
        )

    except SecurityError as exc:
        return [str(exc)]

    return dependency_graph.get_dependencies(path)

@mcp.tool()
def get_dependents(
    path: str,
) -> list[str]:
    """
    Return repository files that depend on the specified file.
    """

    try:
        safe_path(
            config.repository_root,
            path,
        )

    except SecurityError as exc:
        return [str(exc)]

    return dependency_graph.get_dependents(path)

@mcp.tool()
def get_project_structure() -> str:
    """
    Return the JavaScript/TypeScript project structure.
    """

    files = scanner.scan()

    paths = sorted(
        file.path
        for file in files
    )

    if not paths:
        return "No JavaScript/TypeScript files found."

    return "\n".join(paths)
@mcp.tool()
def search_code(
    query: str,
    limit: int = 20,
) -> list[dict]:
    """
    Search JavaScript/TypeScript source code.

    Args:
        query: Text to search for.
        limit: Maximum number of results.
    """

    if not query.strip():
        return []

    limit = max(
        1,
        min(limit, 100),
    )

    return search_engine.search(
        query=query,
        limit=limit,
    )




@mcp.tool()
def get_file(
    path: str,
    start_line: int = 1,
    end_line: int = 200,
) -> str:
    """
    Read a source file from the repository.

    Only JavaScript/TypeScript files are currently supported.
    """

    try:
        file_path = safe_path(
            config.repository_root,
            path,
        )

    except SecurityError as exc:
        return str(exc)

    if not file_path.exists():
        return f"File not found: {path}"

    if not file_path.is_file():
        return f"Not a file: {path}"



    detected = detect_language(file_path)

    if detected is None:
        return (
            "Unsupported file type. "
            "Only JavaScript and TypeScript "
            "files are currently supported."
        )

    try:
        lines = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

    except OSError as exc:
        return f"Could not read file: {exc}"

    start_line = max(1, start_line)
    end_line = min(
        len(lines),
        end_line,
    )

    if start_line > end_line:
        return "Invalid line range."

    selected = lines[
        start_line - 1:end_line
    ]

    output = []

    for number, line in enumerate(
        selected,
        start=start_line,
    ):
        output.append(
            f"{number:>5} | {line}"
        )

    return "\n".join(output)


# ---------------------------------------------------------
# Tool: find symbol
# ---------------------------------------------------------

@mcp.tool()
def find_symbol(
    symbol_name: str,
) -> list[dict]:
    """
    Find classes, functions, methods, interfaces,
    types, and enums in the repository.
    """

    results = []

    files = scanner.scan()

    for file in files:

        path = Path(file.absolute_path)

        try:
            symbols = parser.extract_symbols(
                path,
                file.language,
            )

        except Exception as exc:
            logger.warning(
                "Could not parse %s: %s",
                file.path,
                exc,
            )
            continue

        for symbol in symbols:

            if symbol.name.lower() == symbol_name.lower():

                results.append(
                    {
                        "name": symbol.name,
                        "kind": symbol.kind,
                        "file": file.path,
                        "start_line": symbol.start_line,
                        "end_line": symbol.end_line,
                    }
                )

    return results



@mcp.tool()
def lookup_symbol_definitions(symbol_name: str) -> list[dict]:
    """Find indexed definitions matching a symbol name."""
    if not symbol_name.strip():
        return []

    return symbol_index.find(symbol_name)


@mcp.tool()
def analyze_file(
    path: str,
) -> dict:
    """
    Analyze a JavaScript/TypeScript file using Tree-sitter.
    """

    try:
        file_path = safe_path(
            config.repository_root,
            path,
        )

    except SecurityError as exc:
        return {
            "error": str(exc)
        }

    if not file_path.exists():
        return {
            "error": f"File not found: {path}"
        }

    from app.repository.detector import detect_language

    language = detect_language(file_path)

    if language is None:
        return {
            "error": "Unsupported file type."
        }

    try:

        symbols = parser.extract_symbols(
            file_path,
            language,
        )

        imports = parser.extract_imports(
            file_path,
            language,
        )

        return {
            "file": path,
            "language": language,
            "symbols": [
                {
                    "name": symbol.name,
                    "kind": symbol.kind,
                    "start_line": symbol.start_line,
                    "end_line": symbol.end_line,
                }
                for symbol in symbols
            ],
            "imports": [
                {
                    "source": item.source,
                    "line": item.start_line,
                }
                for item in imports
            ],
        }

    except Exception as exc:

        logger.exception(
            "Analysis failed for %s",
            path,
        )

        return {
            "error": str(exc)
        }


@mcp.tool()
def get_dependency_graph() -> dict:
    """
    Return the complete repository dependency graph.
    """

    return {
        "nodes": sorted(
            dependency_graph.file_index.keys()
        ),
        "edges": [
            {
                "from": source,
                "to": target,
            }
            for source, targets
            in dependency_graph.dependencies.items()
            for target in sorted(targets)
        ],
    }

@mcp.resource(
    "repo://structure"
)
def repository_structure_resource() -> str:
    

    return get_project_structure()

@mcp.resource(
    "repo://statistics"
)
def repository_statistics_resource() -> dict:
    """
    Repository statistics.
    """

    return repository_info()



def main():
    logger.info(
        "Starting Repository Intelligence MCP server"
    )

    logger.info(
        "Repository: %s",
        config.repository_root,
    )

    mcp.run()

@mcp.tool()
def analyze_change_impact(
    path: str,
    max_depth: int = 10,
) -> dict:
    """
    Analyze which repository files could be affected
    if the specified file changes.
    """

    try:
        safe_path(
            config.repository_root,
            path,
        )
    except SecurityError as exc:
        return {
            "error": str(exc)
        }

    max_depth = max(
        1,
        min(max_depth, 20),
    )

    return impact_analyzer.analyze(
        path,
        max_depth,
    )

if __name__ == "__main__":
    main()