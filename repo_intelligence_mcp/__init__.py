"""Command-line entry point for the repository intelligence MCP server."""


def main() -> None:
    from app.server import main as run_server

    run_server()
