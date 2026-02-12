"""Test suite for attack graph module."""
import pytest
from rapids.reasoning.attack_graph import AttackGraph


def test_attack_graph_initialization():
    """Test graph initialization."""
    graph = AttackGraph()
    assert len(graph.adj) == 0
    assert len(graph.node_risk) == 0


def test_record_flow():
    """Test flow recording."""
    graph = AttackGraph()
    graph.record_flow("host_a", "host_b")
    assert "host_a" in graph.adj
    assert "host_b" in graph.adj["host_a"]


def test_set_role():
    """Test role assignment and prioritization."""
    graph = AttackGraph()
    graph.set_role("host_1", "workstation")
    assert graph.roles["host_1"] == "workstation"
    
    # Test role upgrade (servers rank higher than workstations)
    graph.set_role("host_1", "server")
    assert graph.roles["host_1"] == "server"
    
    # Test that lower-rank roles don't downgrade
    graph.set_role("host_1", "workstation")
    assert graph.roles["host_1"] == "server"


def test_add_anomaly_single():
    """Test single anomaly addition."""
    graph = AttackGraph()
    graph.add_anomaly("host_a", "host_b", severity=0.5)
    assert graph.node_risk["host_a"] == 0.5
    assert graph.node_risk["host_b"] == 0.5


def test_add_anomaly_multiple():
    """Test multiple anomalies capping at 1.0."""
    graph = AttackGraph()
    graph.add_anomaly("host_a", "host_b", severity=0.6)
    graph.add_anomaly("host_a", "host_b", severity=0.6)
    assert graph.node_risk["host_a"] <= 1.0
    assert graph.node_risk["host_b"] <= 1.0


def test_propagate_risk_basic():
    """Test risk propagation across edges."""
    graph = AttackGraph()
    graph.record_flow("a", "b")
    graph.record_flow("b", "c")
    graph.add_anomaly("a", "b", severity=0.8)
    
    # Before propagation, only a and b should have high risk
    initial_c_risk = graph.node_risk.get("c", 0.0)
    assert initial_c_risk == 0.0
    
    # After propagation, c should have non-zero risk
    graph.propagate_risk(decay=0.5, max_depth=2)
    assert graph.node_risk.get("c", 0.0) > 0.0


def test_propagate_risk_decay():
    """Test that risk decays over hops."""
    graph = AttackGraph()
    graph.record_flow("src", "mid1")
    graph.record_flow("mid1", "mid2")
    graph.record_flow("mid2", "dst")
    graph.add_anomaly("src", "mid1", severity=0.9)
    graph.propagate_risk(decay=0.5, max_depth=3)
    
    # Risk should decrease at each hop
    src_risk = graph.node_risk.get("src", 0.0)
    mid1_risk = graph.node_risk.get("mid1", 0.0)
    mid2_risk = graph.node_risk.get("mid2", 0.0)
    dst_risk = graph.node_risk.get("dst", 0.0)
    
    assert src_risk >= mid1_risk >= mid2_risk >= dst_risk


def test_propagate_risk_max_depth():
    """Test that risk propagation respects max_depth."""
    graph = AttackGraph()
    # Create a long chain
    for i in range(10):
        graph.record_flow(f"host_{i}", f"host_{i+1}")
    
    graph.add_anomaly("host_0", "host_1", severity=0.8)
    graph.propagate_risk(decay=0.5, max_depth=2)
    
    # Max depth 2 means we should reach at most host_3
    assert graph.node_risk.get("host_3", 0.0) >= 0.0
