"""Test suite for reasoning engine."""
import pytest
from rapids.reasoning.engine import ReasoningEngine


@pytest.fixture
def reasoning_engine():
    """Create a reasoning engine instance."""
    return ReasoningEngine(host_count=20, max_hops=3)


@pytest.fixture
def sample_flow():
    """Generate a sample flow record."""
    return {
        "src_ip": "192.168.1.10",
        "dst_ip": "192.168.1.20",
        "destination_port": 443,
        "total_fwd_packets": 100,
        "flow_duration": 5000,
    }


def test_reasoning_engine_initialization(reasoning_engine):
    """Test engine initialization."""
    assert reasoning_engine.host_count == 20
    assert reasoning_engine.graph is not None
    assert reasoning_engine.role_classifier is not None


def test_observe_flow(reasoning_engine, sample_flow):
    """Test flow observation."""
    src, dst = reasoning_engine.observe_flow(sample_flow)
    assert src is not None
    assert dst is not None


def test_observe_flow_adds_to_graph(reasoning_engine, sample_flow):
    """Test that observing a flow updates the graph."""
    reasoning_engine.observe_flow(sample_flow)
    assert len(reasoning_engine.graph.adj) > 0


def test_handle_anomaly_returns_paths(reasoning_engine, sample_flow):
    """Test anomaly handling."""
    src, dst = reasoning_engine.observe_flow(sample_flow)
    paths, recommendations = reasoning_engine.handle_anomaly(src, dst, sample_flow)
    
    assert isinstance(paths, list)
    assert isinstance(recommendations, list)


def test_anomaly_propagates_risk(reasoning_engine, sample_flow):
    """Test that anomalies propagate risk."""
    src, dst = reasoning_engine.observe_flow(sample_flow)
    reasoning_engine.handle_anomaly(src, dst, sample_flow, severity=0.5)
    
    assert reasoning_engine.graph.node_risk.get(src, 0.0) > 0
    assert reasoning_engine.graph.node_risk.get(dst, 0.0) > 0


def test_simulate_containment(reasoning_engine, sample_flow):
    """Test containment simulation."""
    src, dst = reasoning_engine.observe_flow(sample_flow)
    paths, recommendations = reasoning_engine.handle_anomaly(src, dst, sample_flow)
    
    if recommendations:
        result = reasoning_engine.simulate_containment(recommendations[0])
        assert result is not None
        assert "risk_before" in result
        assert "risk_after" in result
        assert result["risk_after"] < result["risk_before"]


def test_multiple_anomalies(reasoning_engine):
    """Test handling multiple anomalies."""
    flows = [
        {"src_ip": "192.168.1.1", "dst_ip": "192.168.1.2", "destination_port": 443},
        {"src_ip": "192.168.1.2", "dst_ip": "192.168.1.3", "destination_port": 3306},
        {"src_ip": "192.168.1.3", "dst_ip": "192.168.1.4", "destination_port": 22},
    ]
    
    for flow in flows:
        src, dst = reasoning_engine.observe_flow(flow)
        reasoning_engine.handle_anomaly(src, dst, flow)
    
    # Should have multiple nodes with risk
    high_risk_nodes = [h for h, r in reasoning_engine.graph.node_risk.items() if r > 0]
    assert len(high_risk_nodes) > 0
