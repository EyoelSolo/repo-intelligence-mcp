"""Pluggable interface for querying a locally managed RAG corpus."""

from dataclasses import asdict, dataclass
from importlib import import_module
import os
from typing import Any, Protocol


@dataclass
class RetrievedPassage:
    """A relevant corpus excerpt with enough provenance to cite it."""

    text: str
    source: str
    score: float | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LocalRetriever(Protocol):
    """Adapter contract implemented by the user's local vector/RAG store."""

    def search(self, query: str, *, limit: int = 5) -> list[RetrievedPassage]:
        """Return ranked excerpts with source references for a natural query."""


def load_local_retriever() -> LocalRetriever | None:
    """Load a configured ``module:factory`` adapter without requiring an MCP server."""
    target = os.environ.get("REPO_INTELLIGENCE_RETRIEVER", "").strip()
    if not target:
        return None
    module_name, separator, factory_name = target.partition(":")
    if not separator or not module_name or not factory_name:
        raise ValueError("REPO_INTELLIGENCE_RETRIEVER must use module:factory format.")
    factory = getattr(import_module(module_name), factory_name)
    retriever = factory()
    if not callable(getattr(retriever, "search", None)):
        raise ValueError("Configured retriever must provide search(query, limit=...).")
    return retriever
