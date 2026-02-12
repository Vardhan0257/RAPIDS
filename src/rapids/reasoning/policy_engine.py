from typing import Dict, List, Optional, Any
from .attack_graph import AttackGraph


def _normalize_key(key: str) -> str:
    """Normalize dictionary keys for flexible field matching."""
    return "_".join(key.strip().lower().replace("/", " ").split())


def _get_value_by_keys(flow: Dict[str, Any], keys: set) -> Optional[Any]:
    """Get value from flow dict using normalized key matching."""
    for key in flow.keys():
        normalized = _normalize_key(key)
        if normalized in keys:
            return flow[key]
    return None


class PolicyEngine:
    """Generate containment policy recommendations based on attack paths."""
    
    def __init__(self, graph: AttackGraph) -> None:
        """Initialize policy engine with attack graph."""
        self.graph = graph

    def _estimate_reduction(self, risk: float) -> float:
        """Estimate risk reduction percentage from containment action."""
        return min(0.9, 0.2 + (risk * 0.5))

    def _dest_port(self, flow: Dict[str, Any]) -> Optional[int]:
        """Extract destination port from flow record."""
        port_keys = {"destination_port", "dest_port", "dst_port"}
        port = _get_value_by_keys(flow, port_keys)
        try:
            return int(port)
        except (TypeError, ValueError):
            return None

    def recommend(
        self,
        paths: List[Dict[str, Any]],
        flow: Dict[str, Any],
        top_k: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Generate containment recommendations based on attack paths.
        
        Args:
            paths: List of attack paths from engine.
            flow: Current flow record.
            top_k: Number of recommendations to return.
            
        Returns:
            List of recommended containment actions with risk metrics.
        """
        if not paths:
            return []

        recommendations = []
        for item in paths[:top_k]:
            path = item["path"]
            risk = item["risk"]
            src = path[0]
            dst = path[1] if len(path) > 1 else path[0]
            dest_port = self._dest_port(flow)

            if dest_port is not None:
                action = f"Block TCP {dest_port} from {src} to {dst}"
            else:
                action = f"Block connection from {src} to {dst}"

            recommendations.append(
                {
                    "action": action,
                    "risk_reduction": self._estimate_reduction(risk),
                    "path": path,
                    "risk": risk,
                }
            )

        return recommendations

    def simulate_containment(self, recommendation: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Simulate risk reduction from containment action.
        
        Args:
            recommendation: A recommendation dict with risk score.
            
        Returns:
            Dict with risk_before and risk_after.
        """
        if not recommendation:
            return None

        risk_before = recommendation["risk"]
        reduction = recommendation["risk_reduction"]
        risk_after = max(0.0, risk_before * (1.0 - reduction))
        return {
            "risk_before": risk_before,
            "risk_after": risk_after,
        }
