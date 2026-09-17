import logging
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from app.config import Config
from app.parser.code_parser import CodeParser
from app.repository.scanner import RepositoryScanner
from app.repository.security import safe_path, SecurityError
from app.search.search_engine import SearchEngine


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
search_engine = SearchEngine(config)

#mcp server
mcp = MCPServer(
    "Repository Intelligence"
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

