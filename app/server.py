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