# Repository Intelligence MCP

A local MCP server for reading and analyzing code and text files in a configured repository. It exposes file discovery, bounded file reads, text search, symbol lookup, import/dependency analysis, and change impact analysis. JavaScript and TypeScript receive Tree-sitter symbol and import parsing; additional common source, markup, configuration, and text extensions are available for listing, reading, and search.

## Choose the local repository

The default repository is the included `demo-repository`. To use another local folder, set `REPO_INTELLIGENCE_ROOT` to its absolute path before starting the server.

PowerShell example:

```powershell
$env:REPO_INTELLIGENCE_ROOT = 'C:\path\to\your\repository'
uv run repo-intelligence-mcp
```

The server uses stdio transport for MCP clients. Start it from the project environment or configure your MCP client to launch the `repo-intelligence-mcp` command with the project environment available.

All file tools are confined to the configured repository root. Common credential files and private-key folders are blocked, and reads are limited to UTF-8 text files no larger than 1 MB. The scanner skips common generated/dependency directories.

## Optional AI provider

`ask_ai` uses an OpenAI-compatible chat-completions endpoint. Configure these environment variables before starting the server:

```powershell
$env:AI_API_KEY = 'your-provider-key'
$env:AI_MODEL = 'your-model-name'
# Optional; defaults to https://api.openai.com/v1
$env:AI_BASE_URL = 'https://api.openai.com/v1'
```

You may point `AI_BASE_URL` at another provider that implements `/chat/completions`, including a compatible local endpoint. Without a key and model, AI calls return a setup message and make no network request. `ask_ai` sends only the prompt and any file paths explicitly supplied to that call; selected file contents are sent to the configured endpoint. Context is limited to 10 files and 60,000 characters per call. Do not attach sensitive material unless you intend to share it with that provider.

## Current analysis limits

Repository-wide symbol definitions, reference candidates, and dependency graphs are built when the server starts. Restart the server after changing files to refresh these indexes. Semantic reference resolution is not implemented; reference results are syntax-based candidates. Tree-sitter analysis and local import resolution currently cover JavaScript and TypeScript, while broader-language support is limited to file discovery, reading, and text search.
