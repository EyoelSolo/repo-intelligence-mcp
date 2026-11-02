"""ChromaDB adapter for a locally indexed corpus.

Configure the database path, collection, and embedding model with environment
variables, then expose ``create_retriever`` through
``REPO_INTELLIGENCE_RETRIEVER=app.knowledge.chroma_adapter:create_retriever``.
"""

import os
from pathlib import Path
from typing import Any

DEFAULT_CHROMA_PATH = (
    Path.home() / "OneDrive" / "Desktop" / "Projects" / "RAG" / "Data" / "chroma_db"
)


class ChromaRetriever:
    """Search an existing Chroma collection using its ingestion embedding model."""

    def __init__(
        self,
        *,
        path: str,
        collection_name: str,
        embedding_model_name: str,
    ) -> None:
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Chroma retrieval requires the optional 'rag' dependencies: "
                "chromadb and sentence-transformers."
            ) from exc

        database_path = Path(path).expanduser()
        if not database_path.is_dir():
            raise ValueError(f"Chroma database directory does not exist: {database_path}")

        self._client = chromadb.PersistentClient(path=str(database_path))
        self._collection = self._client.get_collection(name=collection_name)
        self._embedding_model = SentenceTransformer(embedding_model_name)

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        count = self._collection.count()
        if count < 1:
            return []

        query_embedding = self._embedding_model.encode([query.strip()]).tolist()
        result = self._collection.query(
            query_embeddings=query_embedding,
            n_results=min(max(1, int(limit)), count),
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0] or []
        metadatas = (result.get("metadatas") or [[]])[0] or []
        distances = (result.get("distances") or [[]])[0] or []

        passages = []
        for index, document in enumerate(documents):
            if not isinstance(document, str) or not document.strip():
                continue
            metadata = metadatas[index] if index < len(metadatas) else {}
            metadata = metadata if isinstance(metadata, dict) else {}
            source_parts = [
                str(metadata[key]).strip()
                for key in ("act", "section", "title")
                if metadata.get(key) is not None and str(metadata[key]).strip()
            ]
            source = " — ".join(source_parts) or "ChromaDB record"
            distance = distances[index] if index < len(distances) else None
            score = 1.0 / (1.0 + max(0.0, float(distance))) if distance is not None else None
            passages.append({
                "text": document,
                "source": source,
                "score": score,
                "metadata": metadata,
            })
        return passages


def create_retriever() -> ChromaRetriever:
    """Create a retriever for the configured local Chroma collection."""
    path = os.environ.get("REPO_INTELLIGENCE_CHROMA_PATH", str(DEFAULT_CHROMA_PATH)).strip()
    collection_name = os.environ.get(
        "REPO_INTELLIGENCE_CHROMA_COLLECTION", "estonian_forestry_laws"
    ).strip()
    embedding_model_name = os.environ.get(
        "REPO_INTELLIGENCE_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ).strip()
    if not path:
        raise ValueError("Set REPO_INTELLIGENCE_CHROMA_PATH to the Chroma database directory.")
    if not collection_name or not embedding_model_name:
        raise ValueError("Chroma collection and embedding model settings must not be empty.")
    return ChromaRetriever(
        path=path,
        collection_name=collection_name,
        embedding_model_name=embedding_model_name,
    )
