from typing import Dict, Optional, Set, Tuple, List
from datetime import datetime, timedelta


class AttackGraph:
    """Directed graph representing network flows and attack risk propagation with temporal decay."""
    
    def __init__(self) -> None:
        """Initialize an empty attack graph."""
        self.adj: Dict[str, Dict[str, float]] = {}
        self.node_risk: Dict[str, float] = {}
        self.edge_risk: Dict[Tuple[str, str], float] = {}
        self.roles: Dict[str, str] = {}
        self.role_rank: Dict[str, int] = {"workstation": 1, "server": 2, "database": 3}
        # Time-aware risk tracking
        self.node_risk_timestamp: Dict[str, datetime] = {}
        self.anomaly_evidence: Dict[Tuple[str, str], List[Tuple[float, datetime]]] = {}
        self.decay_half_life_hours: float = 24.0  # Risk halves every 24 hours

    def _ensure_node(self, host: str) -> None:
        """Ensure a node exists in the graph."""
        if host not in self.node_risk:
            self.node_risk[host] = 0.0
            self.node_risk_timestamp[host] = datetime.now()
        if host not in self.adj:
            self.adj[host] = {}

    def set_role(self, host: str, role: Optional[str]) -> None:
        """Set or upgrade the role of a host."""
        if role is None:
            return
        current = self.roles.get(host)
        if current is None or self.role_rank.get(role, 0) > self.role_rank.get(current, 0):
            self.roles[host] = role

    def record_flow(self, src: Optional[str], dst: Optional[str]) -> None:
        """Record a network flow between two hosts."""
        if src is None or dst is None:
            return
        self._ensure_node(src)
        self._ensure_node(dst)
        if dst not in self.adj[src]:
            self.adj[src][dst] = 0.0

    def _compute_temporal_decay(self, risk: float, last_timestamp: datetime) -> float:
        """
        Apply exponential decay to risk based on time elapsed.
        Risk decays with a half-life equal to decay_half_life_hours.
        """
        elapsed = datetime.now() - last_timestamp
        elapsed_hours = elapsed.total_seconds() / 3600.0
        
        # Exponential decay: risk * (0.5 ^ (elapsed / half_life))
        decay_factor = 0.5 ** (elapsed_hours / self.decay_half_life_hours)
        return risk * decay_factor

    def add_anomaly(self, src: Optional[str], dst: Optional[str], severity: float = 0.15) -> None:
        """Record an anomalous flow and update risk scores with temporal awareness."""
        if src is None or dst is None:
            return
        self._ensure_node(src)
        self._ensure_node(dst)
        self.adj.setdefault(src, {})
        self.adj[src].setdefault(dst, 0.0)

        now = datetime.now()
        
        # Apply temporal decay to existing risk
        src_decayed = self._compute_temporal_decay(
            self.node_risk[src],
            self.node_risk_timestamp[src]
        )
        dst_decayed = self._compute_temporal_decay(
            self.node_risk[dst],
            self.node_risk_timestamp[dst]
        )
        
        # Add new evidence
        self.node_risk[src] = min(1.0, src_decayed + severity)
        self.node_risk[dst] = min(1.0, dst_decayed + severity)
        
        # Update timestamps
        self.node_risk_timestamp[src] = now
        self.node_risk_timestamp[dst] = now

        edge_key = (src, dst)
        
        # Track anomaly evidence for explainability
        if edge_key not in self.anomaly_evidence:
            self.anomaly_evidence[edge_key] = []
        self.anomaly_evidence[edge_key].append((severity, now))
        
        # Keep only recent evidence (last 100 observations)
        if len(self.anomaly_evidence[edge_key]) > 100:
            self.anomaly_evidence[edge_key] = self.anomaly_evidence[edge_key][-100:]
        
        # Update edge risk
        edge_decayed = self._compute_temporal_decay(
            self.edge_risk.get(edge_key, 0.0),
            datetime.now() - timedelta(hours=1)  # Assume 1 hour of decay
        )
        self.edge_risk[edge_key] = min(1.0, edge_decayed + severity)
        self.adj[src][dst] = max(self.adj[src][dst], self.edge_risk[edge_key])

    def get_anomaly_history(self, src: str, dst: str) -> List[Tuple[float, str]]:
        """Get timestamp history of anomalies on an edge."""
        edge_key = (src, dst)
        history = self.anomaly_evidence.get(edge_key, [])
        return [(severity, ts.isoformat()) for severity, ts in history]

    def propagate_risk(self, decay: float = 0.5, max_depth: int = 2) -> None:
        """Propagate risk through the graph using BFS with exponential decay."""
        if not self.node_risk:
            return

        updated = dict(self.node_risk)
        for source, base_risk in self.node_risk.items():
            if base_risk <= 0:
                continue
            frontier: List[Tuple[str, int, float]] = [(source, 0, base_risk)]
            visited: Set[str] = {source}

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
