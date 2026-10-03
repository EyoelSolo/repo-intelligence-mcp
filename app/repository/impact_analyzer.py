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
        affected: dict[str, int] = {}

        queue = deque()

        queue.append(
            (
                normalized,
                0,
            )
        )

        visited = {
            normalized
        }
        while queue:

            current, depth = queue.popleft()

            if depth >= max_depth:
                continue

            for dependent in self.graph.dependents.get(
                current,
                set(),
            ):

                if dependent in visited:
                    continue

                visited.add(dependent)

                affected[
                    dependent
                ] = depth + 1

                queue.append(
                    (
                        dependent,
                        depth + 1,
                    )
                )
        direct = [
            path
            for path, depth in affected.items()
            if depth == 1
        ]