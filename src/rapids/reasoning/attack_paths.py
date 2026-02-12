class AttackPathEngine:
    def __init__(self, graph, max_hops=3):
        self.graph = graph
        self.max_hops = max_hops

    def _combine_risk(self, current, component):
        return 1.0 - ((1.0 - current) * (1.0 - component))

    def compute_paths(self, target_role="database", min_node_risk=0.1, top_k=3):
        targets = [h for h, role in self.graph.roles.items() if role == target_role]
        if not targets:
            return []

        sources = [h for h, r in self.graph.node_risk.items() if r >= min_node_risk]
        if not sources:
            return []

        paths = []
        for source in sources:
            stack = [(source, [source], self.graph.node_risk.get(source, 0.0))]
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
