from .attack_graph import AttackGraph
from .attack_paths import AttackPathEngine
from .host_identity import extract_hosts
from .role_classifier import HostRoleClassifier
from .policy_engine import PolicyEngine


class ReasoningEngine:
    def __init__(self, host_count=20, max_hops=3):
        self.graph = AttackGraph()
        self.role_classifier = HostRoleClassifier()
        self.path_engine = AttackPathEngine(self.graph, max_hops=max_hops)
        self.policy_engine = PolicyEngine(self.graph)
        self.host_count = host_count

    def observe_flow(self, flow):
        src, dst = extract_hosts(flow, host_count=self.host_count)
        self.graph.record_flow(src, dst)

        role = self.role_classifier.classify_destination(flow)
        if role:
            self.graph.set_role(dst, role)
        if src not in self.graph.roles:
            self.graph.set_role(src, "workstation")

        return src, dst

    def handle_anomaly(self, src, dst, flow, severity=0.15):
        self.graph.add_anomaly(src, dst, severity=severity)
        self.graph.propagate_risk()
        paths = self.path_engine.compute_paths()
        recommendations = self.policy_engine.recommend(paths, flow)
        return paths, recommendations

    def simulate_containment(self, recommendation):
        return self.policy_engine.simulate_containment(recommendation)
