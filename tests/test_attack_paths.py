import unittest

from rapids.reasoning.attack_graph import AttackGraph
from rapids.reasoning.attack_paths import AttackPathEngine


class TestAttackPaths(unittest.TestCase):
    def test_path_to_database(self):
        graph = AttackGraph()
        graph.set_role("host_a", "workstation")
        graph.set_role("host_b", "server")
        graph.set_role("db_1", "database")

        graph.record_flow("host_a", "host_b")
        graph.record_flow("host_b", "db_1")

        graph.add_anomaly("host_a", "host_b", severity=0.4)
        graph.add_anomaly("host_b", "db_1", severity=0.4)

        engine = AttackPathEngine(graph, max_hops=3)
        paths = engine.compute_paths()

        self.assertTrue(paths)
        self.assertEqual(paths[0]["path"][0], "host_a")
        self.assertEqual(paths[0]["path"][-1], "db_1")


if __name__ == "__main__":
    unittest.main()
