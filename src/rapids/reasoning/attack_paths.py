from typing import Dict, List, Optional
from .attack_graph import AttackGraph


class AttackPathEngine:
    """Compute attack paths through network graph using risk-based search."""
    
    def __init__(self, graph: AttackGraph, max_hops: int = 3) -> None:
        """Initialize the path engine with a graph and hop limit."""
        self.graph = graph
        self.max_hops = max_hops

    def _combine_risk(self, current: float, component: float) -> float:
        """Combine risks using complement rule: 1 - (1-a)*(1-b)."""
        return 1.0 - ((1.0 - current) * (1.0 - component))

    def compute_paths(
        self,
        target_role: str = "database",
        min_node_risk: float = 0.1,
        top_k: int = 3,
    ) -> List[Dict[str, any]]:
        """
        Compute top-k paths from high-risk sources to target-role hosts.
        
        Args:
            target_role: Role of destination hosts.
            min_node_risk: Minimum node risk to consider as source.
            top_k: Number of top paths to return.
            
        Returns:
            List of paths with risk scores, sorted by risk descending.
        """
        targets = [h for h, role in self.graph.roles.items() if role == target_role]
        if not targets:
            return []

        sources = [h for h, r in self.graph.node_risk.items() if r >= min_node_risk]
        if not sources:
            return []

        paths: List[Dict[str, any]] = []
        for source in sources:
            stack: List[tuple] = [(source, [source], self.graph.node_risk.get(source, 0.0))]
            while stack:
                node, path, risk = stack.pop()
                if len(path) - 1 >= self.max_hops:
                    continue

                for neighbor, edge_risk in self.graph.adj.get(node, {}).items():
                    if neighbor in path:
                        continue
                    next_risk = self._combine_risk(risk, edge_risk)
                    next_risk = self._combine_risk(next_risk, self.graph.node_risk.get(neighbor, 0.0))
                    next_path = path + [neighbor]

                    if neighbor in targets:
                        paths.append({"path": next_path, "risk": next_risk})
                    else:
                        stack.append((neighbor, next_path, next_risk))

        paths.sort(key=lambda item: item["risk"], reverse=True)
        return paths[:top_k]
