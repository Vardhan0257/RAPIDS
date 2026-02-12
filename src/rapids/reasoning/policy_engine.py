def _normalize_key(key):
    return "_".join(key.strip().lower().replace("/", " ").split())


def _get_value_by_keys(flow, keys):
    for key in flow.keys():
        normalized = _normalize_key(key)
        if normalized in keys:
            return flow[key]
    return None


class PolicyEngine:
    def __init__(self, graph):
        self.graph = graph

    def _estimate_reduction(self, risk):
        return min(0.9, 0.2 + (risk * 0.5))

    def _dest_port(self, flow):
        port_keys = {"destination_port", "dest_port", "dst_port"}
        port = _get_value_by_keys(flow, port_keys)
        try:
            return int(port)
        except (TypeError, ValueError):
            return None

    def recommend(self, paths, flow, top_k=1):
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

    def simulate_containment(self, recommendation):
        if not recommendation:
            return None

        risk_before = recommendation["risk"]
        reduction = recommendation["risk_reduction"]
        risk_after = max(0.0, risk_before * (1.0 - reduction))
        return {
            "risk_before": risk_before,
            "risk_after": risk_after,
        }
