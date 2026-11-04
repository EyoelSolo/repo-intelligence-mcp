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

Repository-wide symbol definitions, reference candidates, and dependency graphs are built when the server starts. Call `refresh_repository_index` after changing files to rebuild the symbol and dependency indexes without restarting the server. Semantic reference resolution is not implemented; reference results are syntax-based candidates. Tree-sitter analysis and local import resolution currently cover JavaScript and TypeScript, while broader-language support is limited to file discovery, reading, and text search.

## External data and local retrieval adapters

Set `REPO_INTELLIGENCE_DATA_SOURCES` to a JSON object of named source settings
to enable multiple online connectors. Each source supports its own URL, headers,
timeout, retry count, and optional page/page-size query parameter names. For
example:

```powershell
$env:REPO_INTELLIGENCE_DATA_SOURCES = '{"catalog":{"url":"https://data.example/api/records","timeout":10,"retries":2,"page_param":"page","page_size_param":"limit","max_pages":5},"archive":{"url":"https://archive.example/items","headers":{"Authorization":"Bearer your-token"}}}'
```

Call `fetch_external_records` with `source="catalog"` or `source="archive"`.
The legacy `REPO_INTELLIGENCE_DATA_URL` and `REPO_INTELLIGENCE_DATA_HEADERS`
variables remain supported as the default `configured-source`. The connector
accepts JSON arrays, common `results`/`data`
wrappers, single JSON objects, and GeoJSON Features or FeatureCollections. Each
record is returned in a stable envelope with `id`, `source`, `retrieved_at`,
`attributes`, optional `geometry`, and `source_url`; original source fields are
preserved under `attributes`. Responses are limited to 2 MB and 1,000 records.
For a single authenticated endpoint, set `REPO_INTELLIGENCE_DATA_HEADERS` to a JSON
object of HTTP header names and values. Keep credentials in environment
variables or a secret manager rather than repository files:

```powershell
$env:REPO_INTELLIGENCE_DATA_HEADERS = '{"Authorization":"Bearer your-token"}'
```

To connect a local vector/RAG corpus, set `REPO_INTELLIGENCE_RETRIEVER` to a
Python factory in `module:factory` form. The factory returns an object with
`search(query, limit=...)`, which returns passages containing `text` and
`source`, with optional `score` and `metadata`. The MCP exposes this through
`search_local_knowledge`. `answer_with_local_knowledge` retrieves bounded
passages, asks the configured AI provider to answer from that evidence, and
returns the cited source passages with the answer so claims can be checked. It
requires both a retriever and the optional AI provider configuration above; the
vector store and corpus remain local and are implemented by the configured
adapter, not by an external MCP server.

### ChromaDB adapter

The optional built-in Chroma adapter can query a collection indexed by your own
ingestion script. Install its dependencies with `uv sync --extra rag`, then set
the database folder, collection name, and the same embedding model used during
ingestion. For example, in PowerShell:

```powershell
$env:REPO_INTELLIGENCE_RETRIEVER = 'app.knowledge.chroma_adapter:create_retriever'
$env:REPO_INTELLIGENCE_CHROMA_PATH = 'C:\path\to\RAG\Data\chroma_db'
$env:REPO_INTELLIGENCE_CHROMA_COLLECTION = 'documents'
$env:REPO_INTELLIGENCE_EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
$env:AI_API_KEY = 'ollama'
$env:AI_MODEL = 'qwen2.5'
$env:AI_BASE_URL = 'http://localhost:11434/v1'
uv run repo-intelligence-mcp
```

The adapter embeds each search query with the configured SentenceTransformer
model, matching the model used by the example ingestion script. `AI_MODEL` must
match a model installed in Ollama. The adapter only reads the Chroma collection;
it does not ingest files or reset the collection.

### Chat directly with Qwen using MCP tools

To have Qwen choose and call MCP tools during a conversation, start the
interactive client instead of launching the MCP server directly. By default,
the client uses `~/OneDrive/Desktop/Projects/RAG/Data/chroma_db`, the
`estonian_forestry_laws` collection, and the embedding model above. Override
these with the `REPO_INTELLIGENCE_CHROMA_*` and
`REPO_INTELLIGENCE_EMBEDDING_MODEL` environment variables if your paths differ.

```powershell
ollama pull qwen3:8b
uv sync --extra rag
uv run --extra rag repo-intelligence-qwen
```

The client connects to Ollama and starts the MCP server as a child process using
the same Python environment and inherited configuration. Type questions at the
`You:` prompt; Qwen can call the advertised tools, inspect their results, and
reply in the same conversation. Enter `/clear` to reset chat history or `/exit`
to quit. Ollama must be running locally. The first retrieval may also download
the configured SentenceTransformer embedding model if it is not cached yet.

Example configuration:

```powershell
$env:REPO_INTELLIGENCE_DATA_URL = 'https://data.example/api/records'
$env:REPO_INTELLIGENCE_RETRIEVER = 'my_rag_adapter:create_retriever'
uv run repo-intelligence-mcp
```

Pagination uses bounded page-number query parameters configured per source; at
most 100 pages and 1,000 records are fetched per call. Network errors, HTTP 429,
and server errors are retried with a capped delay; numeric `Retry-After` values
are honored up to 30 seconds. Each response remains limited to 2 MB.
