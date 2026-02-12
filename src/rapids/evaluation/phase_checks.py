import argparse

from rapids.evaluation.benchmarking import build_report
from rapids.reasoning.attack_graph import AttackGraph
from rapids.reasoning.attack_paths import AttackPathEngine
from rapids.reasoning.policy_engine import PolicyEngine


def check_phase4_graph():
    graph = AttackGraph()
    for i in range(12):
        graph.record_flow(f"host_{i}", f"host_{(i + 1) % 12}")
    edges = sum(len(v) for v in graph.adj.values())
    return {
        "nodes": len(graph.adj),
        "edges": edges,
    }


def check_phase4_risk():
    graph = AttackGraph()
    graph.record_flow("host_a", "host_b")
    graph.record_flow("host_b", "host_c")
    graph.add_anomaly("host_a", "host_b", severity=0.5)
    graph.add_anomaly("host_a", "host_b", severity=0.35)
    graph.propagate_risk(decay=0.5, max_depth=2)
    return {
        "host_a": graph.node_risk.get("host_a", 0.0),
        "host_b": graph.node_risk.get("host_b", 0.0),
        "host_c": graph.node_risk.get("host_c", 0.0),
    }


def check_phase4_attack_path():
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
    return paths[0] if paths else None


def check_phase5_policy():
    policy = PolicyEngine(AttackGraph())
    paths = [
        {
            "path": ["Host A", "Host B"],
            "risk": 0.91,
        }
    ]
    flow = {"Destination Port": 445}
    recs = policy.recommend(paths, flow)
    simulation = policy.simulate_containment(recs[0]) if recs else None
    return recs[0] if recs else None, simulation


def check_phase6(dataset, max_rows, batch_size):
    report = build_report(dataset, max_rows, batch_size)
    return report


def main():
    parser = argparse.ArgumentParser(description="Phase validation checks")
    parser.add_argument("--dataset", default="datasets/sample.csv")
    parser.add_argument("--max-rows", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=256)
    args = parser.parse_args()

    graph = check_phase4_graph()
    risk = check_phase4_risk()
    path = check_phase4_attack_path()
    rec, sim = check_phase5_policy()
    report = check_phase6(args.dataset, args.max_rows, args.batch_size)

    print("[PHASE4] graph", graph)
    print("[PHASE4] risk", risk)
    print("[PHASE4] attack_path", path)
    print("[PHASE5] recommendation", rec)
    print("[PHASE5] simulation", sim)
    print("[PHASE6] report", report)


if __name__ == "__main__":
    main()
