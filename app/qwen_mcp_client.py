"""Interactive Ollama/Qwen chat client for this repository's MCP server."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import traceback
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.knowledge.chroma_adapter import DEFAULT_CHROMA_PATH


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_TOOL_ROUNDS = 8
MAX_OLLAMA_RESPONSE_BYTES = 8_000_000


def _ollama_chat(base_url: str, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "tools": tools,
        "stream": False,
    }).encode("utf-8")
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    request = Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=300) as response:
            body = response.read(MAX_OLLAMA_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        detail = exc.read(4_096).decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else "."
        raise RuntimeError(f"Ollama returned HTTP {exc.code}{suffix}") from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError(
            "Could not reach Ollama. Make sure Ollama is running and the model is installed."
        ) from None
    if len(body) > MAX_OLLAMA_RESPONSE_BYTES:
        raise RuntimeError("Ollama response exceeded the 8 MB limit.")
    try:
        result = json.loads(body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise RuntimeError("Ollama returned invalid JSON.") from None
    if not isinstance(result, dict) or not isinstance(result.get("message"), dict):
        raise RuntimeError("Ollama response did not contain a chat message.")
    return result["message"]


def _mcp_result_text(result: Any) -> str:
    blocks = []
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            blocks.append({"type": "text", "text": text})
        else:
            dump = getattr(block, "model_dump", None)
            blocks.append(dump(mode="json") if callable(dump) else str(block))
    envelope = {
        "isError": bool(getattr(result, "isError", False)),
        "content": blocks,
    }
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        envelope["structuredContent"] = structured
    return json.dumps(envelope, ensure_ascii=False, default=str)


def _ollama_tools(mcp_tools: list[Any]) -> list[dict[str, Any]]:
    definitions = []
    for tool in mcp_tools:
        schema = getattr(tool, "inputSchema", None)
        if not isinstance(schema, dict):
            schema = {"type": "object", "properties": {}}
        definitions.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or tool.name,
                "parameters": schema,
            },
        })
    return definitions


async def _chat(model: str, ollama_url: str, server_env: dict[str, str]) -> None:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-c", "from repo_intelligence_mcp import main; main()"],
        cwd=str(PROJECT_ROOT),
        env=server_env,
    )
    print("Connecting Qwen to Repository Intelligence MCP...")
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            available = await session.list_tools()
            tools = _ollama_tools(available.tools)
            print(f"Connected. Qwen can use {len(tools)} MCP tools.")
            print("Type /exit to quit or /clear to start a fresh conversation.\n")

            messages: list[dict[str, Any]] = [{
                "role": "system",
                "content": (
                    "You are Qwen, chatting directly with the user. Use the connected MCP tools "
                    "when repository files, external records, or local knowledge are needed. "
                    "For questions about the local corpus, use search_local_knowledge to retrieve "
                    "evidence, then answer from those passages and identify their sources. "
                    "If evidence is missing, say so. Never claim a tool succeeded unless its result confirms it."
                ),
            }]

            while True:
                try:
                    user_text = await asyncio.to_thread(input, "You: ")
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye.")
                    return
                user_text = user_text.strip()
                if not user_text:
                    continue
                if user_text.lower() in {"/exit", "/quit"}:
                    print("Goodbye.")
                    return
                if user_text.lower() == "/clear":
                    messages = messages[:1]
                    print("Conversation cleared.\n")
                    continue

                messages.append({"role": "user", "content": user_text})
                for _ in range(MAX_TOOL_ROUNDS):
                    try:
                        assistant_message = await asyncio.to_thread(
                            _ollama_chat, ollama_url, model, messages, tools
                        )
                    except RuntimeError as exc:
                        print(f"\nOllama request failed: {exc}\n")
                        messages.pop()
                        break
                    # Keep Ollama's assistant message intact so its tool-call records
                    # remain paired with the following tool results.
                    messages.append(assistant_message)
                    calls = assistant_message.get("tool_calls") or []
                    if not calls:
                        answer = assistant_message.get("content", "")
                        print(f"\nQwen: {answer}\n")
                        break

                    for call in calls:
                        function = call.get("function") or {}
                        name = function.get("name")
                        arguments = function.get("arguments") or {}
                        if not isinstance(name, str) or not isinstance(arguments, dict):
                            messages.append({
                                "role": "tool",
                                "tool_name": str(name or "unknown"),
                                "content": "Tool call rejected: expected a tool name and JSON object arguments.",
                            })
                            continue
                        print(f"[Qwen calls {name}]")
                        try:
                            result = await session.call_tool(name, arguments)
                            tool_text = _mcp_result_text(result)
                        except Exception as exc:
                            tool_text = json.dumps({"isError": True, "error": type(exc).__name__})
                        messages.append({
                            "role": "tool",
                            "tool_name": name,
                            "content": tool_text,
                        })
                else:
                    print("\nQwen reached the tool-call limit for this turn. Ask a follow-up to continue.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with Qwen using Repository Intelligence MCP tools.")
    parser.add_argument(
        "--model",
        default=os.environ.get("QWEN_MODEL", "qwen3:8b"),
        help="Ollama model name (default: QWEN_MODEL or qwen3:8b)",
    )
    parser.add_argument(
        "--ollama-url",
        default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
        help="Ollama API base URL (default: OLLAMA_HOST or http://localhost:11434)",
    )
    args = parser.parse_args()
    server_env = os.environ.copy()
    server_env.setdefault(
        "REPO_INTELLIGENCE_RETRIEVER",
        "app.knowledge.chroma_adapter:create_retriever",
    )
    server_env.setdefault("REPO_INTELLIGENCE_CHROMA_PATH", str(DEFAULT_CHROMA_PATH))
    server_env.setdefault("REPO_INTELLIGENCE_CHROMA_COLLECTION", "estonian_forestry_laws")
    server_env.setdefault(
        "REPO_INTELLIGENCE_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    server_env.setdefault("AI_API_KEY", "ollama")
    server_env.setdefault("AI_MODEL", args.model)
    server_env.setdefault("AI_BASE_URL", "http://localhost:11434/v1")
    try:
        asyncio.run(_chat(args.model, args.ollama_url, server_env))
    except KeyboardInterrupt:
        print("\nGoodbye.")
    except Exception as exc:
        print(f"Qwen MCP chat failed: {exc}", file=sys.stderr)
        traceback.print_exception(exc, file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
