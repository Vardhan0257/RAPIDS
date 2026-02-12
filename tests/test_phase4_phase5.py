import unittest

from rapids.reasoning.attack_graph import AttackGraph
from rapids.reasoning.attack_paths import AttackPathEngine
from rapids.reasoning.policy_engine import PolicyEngine


class TestPhase4Phase5(unittest.TestCase):
    def test_graph_creation(self):
        graph = AttackGraph()
        for i in range(12):
            graph.record_flow(f"host_{i}", f"host_{(i + 1) % 12}")
        nodes = len(graph.adj)
        edges = sum(len(v) for v in graph.adj.values())
        self.assertEqual(nodes, 12)
        self.assertEqual(edges, 12)

    def test_risk_propagation(self):
        graph = AttackGraph()
        graph.record_flow("host_a", "host_b")
        graph.record_flow("host_b", "host_c")
        graph.add_anomaly("host_a", "host_b", severity=0.5)
        graph.add_anomaly("host_a", "host_b", severity=0.35)
        graph.propagate_risk(decay=0.5, max_depth=2)

        self.assertGreaterEqual(graph.node_risk.get("host_a", 0.0), 0.85)
        self.assertGreaterEqual(graph.node_risk.get("host_b", 0.0), 0.35)
        self.assertGreater(graph.node_risk.get("host_c", 0.0), 0.0)

    def test_attack_path_detection(self):
        graph = AttackGraph()
        graph.set_role("workstation_3", "workstation")
        graph.set_role("app_server", "server")
        graph.set_role("database", "database")

        graph.record_flow("workstation_3", "app_server")
        graph.record_flow("app_server", "database")
        graph.add_anomaly("workstation_3", "app_server", severity=0.5)
        graph.add_anomaly("app_server", "database", severity=0.6)

        engine = AttackPathEngine(graph, max_hops=3)
        paths = engine.compute_paths()

        self.assertTrue(paths)
        path = paths[0]
        self.assertEqual(path["path"][0], "workstation_3")
        self.assertEqual(path["path"][-1], "database")

    def test_policy_feedback(self):
        policy = PolicyEngine(AttackGraph())
        paths = [{"path": ["Host A", "Host B"], "risk": 0.91}]
        flow = {"Destination Port": 445}
        recs = policy.recommend(paths, flow)
        self.assertTrue(recs)
        self.assertIn("Block TCP 445", recs[0]["action"])
        sim = policy.simulate_containment(recs[0])
        self.assertIsNotNone(sim)
        self.assertLess(sim["risk_after"], sim["risk_before"])


if __name__ == "__main__":
    unittest.main()
