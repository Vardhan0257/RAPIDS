class AttackGraph:
    def __init__(self):
        self.adj = {}
        self.node_risk = {}
        self.edge_risk = {}
        self.roles = {}
        self.role_rank = {"workstation": 1, "server": 2, "database": 3}

    def _ensure_node(self, host):
        if host not in self.node_risk:
            self.node_risk[host] = 0.0
        if host not in self.adj:
            self.adj[host] = {}

    def set_role(self, host, role):
        if role is None:
            return
        current = self.roles.get(host)
        if current is None or self.role_rank.get(role, 0) > self.role_rank.get(current, 0):
            self.roles[host] = role

    def record_flow(self, src, dst):
        if src is None or dst is None:
            return
        self._ensure_node(src)
        self._ensure_node(dst)
        if dst not in self.adj[src]:
            self.adj[src][dst] = 0.0

    def add_anomaly(self, src, dst, severity=0.15):
        if src is None or dst is None:
            return
        self._ensure_node(src)
        self._ensure_node(dst)
        self.adj.setdefault(src, {})
        self.adj[src].setdefault(dst, 0.0)

        self.node_risk[src] = min(1.0, self.node_risk[src] + severity)
        self.node_risk[dst] = min(1.0, self.node_risk[dst] + severity)

        edge_key = (src, dst)
        self.edge_risk[edge_key] = min(1.0, self.edge_risk.get(edge_key, 0.0) + severity)
        self.adj[src][dst] = max(self.adj[src][dst], self.edge_risk[edge_key])

    def propagate_risk(self, decay=0.5, max_depth=2):
        if not self.node_risk:
            return

        updated = dict(self.node_risk)
        for source, base_risk in self.node_risk.items():
            if base_risk <= 0:
                continue
            frontier = [(source, 0, base_risk)]
            visited = {source}

            while frontier:
                node, depth, risk = frontier.pop(0)
                if depth >= max_depth:
                    continue
                for neighbor in self.adj.get(node, {}):
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    propagated = risk * decay
                    if propagated > updated.get(neighbor, 0.0):
                        updated[neighbor] = min(1.0, propagated)
                    frontier.append((neighbor, depth + 1, propagated))

        self.node_risk.update(updated)
