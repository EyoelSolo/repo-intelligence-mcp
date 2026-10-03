from collections import deque

from app.repository.dependency_graph import DependencyGraph


class ImpactAnalyzer:

    def __init__(
        self,
        dependency_graph: DependencyGraph,
    ):
        self.graph = dependency_graph

    def analyze(
        self,
        path: str,
        max_depth: int = 10,
    ) -> dict:

        normalized = path.replace("\\", "/")
        if normalized not in self.graph.file_index:
            return {
                "error": f"File not found in repository: {path}"
            }