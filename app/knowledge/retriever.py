"""Pluggable interface for querying a locally managed RAG corpus."""

from dataclasses import asdict, dataclass
from importlib import import_module
import math
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


MAX_PASSAGE_CHARS = 8_000
MAX_QUERY_CHARS = 20_000


def normalize_passage(value: Any) -> RetrievedPassage:
    """Validate and bound an adapter result before exposing it to MCP clients."""
    if isinstance(value, RetrievedPassage):
        passage = value
    elif isinstance(value, dict):
        passage = RetrievedPassage(**value)
    else:
        raise ValueError("Retriever results must be passages or passage dictionaries.")
    if not isinstance(passage.text, str) or not passage.text.strip():
        raise ValueError("Retriever passage text must be a non-empty string.")
    if not isinstance(passage.source, str) or not passage.source.strip():
        raise ValueError("Retriever passage source must be a non-empty string.")
    if passage.score is not None:
        if isinstance(passage.score, bool) or not isinstance(passage.score, (int, float)):
            raise ValueError("Retriever passage score must be a finite number.")
        try:
            finite_score = math.isfinite(passage.score)
        except OverflowError:
            finite_score = False
        if not finite_score:
            raise ValueError("Retriever passage score must be a finite number.")
    if passage.metadata is not None and not isinstance(passage.metadata, dict):
        raise ValueError("Retriever passage metadata must be an object.")
    passage.text = passage.text[:MAX_PASSAGE_CHARS]
    return passage


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
