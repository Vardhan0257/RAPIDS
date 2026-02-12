# RAPIDS: Architecture & Design

## Vision

RAPIDS is a **production-grade intrusion detection system** that combines real-time anomaly detection with graph-based risk reasoning to generate actionable containment policies. It processes network flows at scale while maintaining sub-millisecond latency and providing explainable, path-aware security recommendations.

## System Architecture

### High-Level Data Flow

```
Network Flows (CSV/Stream)
    ↓
[Producer: Load & Enqueue via Redis Streams]
    ↓
[Consumer: Batch Processing]
    ├→ [Anomaly Detection: Isolation Forest]
    └→ [Risk Propagation: Attack Graph]
    ↓
[Reasoning Engine: Path Computation & Policy]
    ├→ Attack Path Extraction
    ├→ Risk Scoring
    └→ Containment Recommendations
    ↓
[Output: Alerts, Actions, Metrics]
```

## Core Components

### 1. Detection Module (`src/rapids/detection/`)

**Anomaly Detection: Isolation Forest**

- **Algorithm**: Isolation Forest (unsupervised, no labels required)
- **Key Properties**:
  - O(n log n) training time
  - O(log n) per-sample inference
  - Handles streaming naturally—no retraining needed
- **Configuration**: Contamination set to 0.20 by default
- **Evaluation**: Precision, Recall, F1, False Positive Rate

**Why Isolation Forest?**
- Efficient for high-dimensional data
- No normalcy assumption (vs Gaussian methods)
- Scales well with data volume
- Can catch novel attack patterns

**Limitations & Mitigations**:
- Doesn't leverage labels → we provide supervised baseline (Random Forest) for comparison
- Fixed contamination → we include threshold analysis to tune per-deployment

### 2. Reasoning Module (`src/rapids/reasoning/`)

#### Attack Graph
- **Nodes**: Hosts/entities in network
- **Edges**: Observed flows (weighted by anomaly severity)
- **Node Risk**: Cumulative likelihood of compromise
- **Edge Risk**: Anomaly severity on that connection
- **Temporal Decay**: Risk naturally decays over 24 hours (configurable)

**Risk Propagation Algorithm**:
- Breadth-first search from high-risk nodes
- Exponential decay: `risk_neighbor = risk_source * decay^depth`
- Capped at max_hops (typically 3) to avoid over-spreading
- Temporal aware: applies exponential time-decay to old risks

#### Attack Paths
- Computes top-K paths (default 3) from anomalous sources to high-value targets (databases)
- Path risk: combines node and edge risks using complement rule `1 - (1-a)*(1-b)`
- Allows identification of exploitation chains

#### Policy Engine
- Maps attack paths → containment recommendations
- Extracts destination port for precise firewall rules
- Estimates risk reduction (0.2–0.9 depending on path risk)
- Simulates containment to validate effectiveness

#### Role Classifier
- Infers host role from destination port
- Database: 1433, 1521, 3306, 5432
- Server: 80, 443, 22, 389, 445, 3389
- Workstation: everything else
- Supports priority-based role upgrades

### 3. Streaming Module (`src/rapids/streaming/`)

**Architecture**:
- **Producer**: Reads CSV → JSONifies rows → pushes to Redis Stream
- **Consumer**: Subscribes to stream → batches → detects → propagates risk → emits actions

**Throughput**:
- Measured: ~1000–2000 flows/sec on typical hardware
- Configurable batch size (default 200) for latency tuning
- Sub-millisecond per-sample latency via batch inference

**Redis Streams**:
- Persistent, append-only log
- At-least-once semantics
- Natural backpressure without message loss

### 4. Evaluation Module (`src/rapids/evaluation/`)

#### Benchmarking
- **Throughput**: flows/sec with latency percentiles (p50, p95)
- **Detection Metrics**: Precision, Recall, F1, FPR on true positive rate
- **Cross-Validation**: 5-fold stratified CV for robustness (±std shown)
- **Baselines**:
  - Random Forest (supervised) for upper-bound comparison
  - Default Isolation Forest (contamination=0.1) for sensitivity
- **Threshold Analysis**: F1 optimization across decision thresholds
- **Path Accuracy**: % of detected anomalies with viable attack paths

#### Reproducibility
- Fixed random seeds (42) for deterministic runs
- Stratified folds respect class balance
- Metrics reported with standard deviation

## Deployment Considerations

### Scaling

**Horizontal**:
- Multiple consumers on same Redis stream (consumer groups)
- Partitioned graph (per-subnet) for large networks
- Distributed cache for model coefficients

**Vertical**:
- Batch size tuning: larger batches → higher throughput, higher latency
- Contamination tuning: higher contamination → more alerts, higher recall
- Max hops reduction: smaller max_hops → faster path computation

### Production Hardening

**Implemented**:
- Type hints for type safety
- Comprehensive unit tests (attack graph, paths, policy, detection)
- CI/CD pipeline (GitHub Actions, multiple Python versions)
- Error handling for Redis connection failures

**Recommended**:
- Add persistent model checkpoints + versioning
- Implement model drift detection
- Add distributed tracing (Jaeger) for latency profiling
- Persist benchmark reports for SLA tracking

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Train IF | O(n log n) | One-time offline |
| Detect (per-batch) | O(batch_size * n_features * log n) | Tree traversal |
| Propagate risk | O(nodes + edges) | BFS from sources |
| Compute paths | O(k * branching^max_hops) | DFS with memoization |
| Recommend | O(k) | Linear in top-k paths |

### Space Complexity

| Component | Space | Notes |
|-----------|-------|-------|
| IF trees | O(n_trees * n) | ~100 trees typical |
| Attack graph | O(nodes + edges) | Sparse: ~2-5 edges per node |
| Models in memory | <100 MB | Typical for <100k samples |

## Testing Strategy

### Unit Tests

- **Attack Graph**: Node creation, edge recording, risk propagation, temporal decay
- **Attack Paths**: Path computation, risk combination, sorting by risk
- **Anomaly Model**: Training, cross-validation, threshold analysis
- **Policy Engine**: Recommendation generation, containment simulation
- **Reasoning Engine**: Flow observation, anomaly handling, multi-anomaly scenarios

### Coverage Goals

- Target: >85% line coverage
- Critical path: 100% (detection, risk propagation, policy generation)
- Optional: 70% (CLI, config loading)

### Integration Tests (Recommended)

- End-to-end: load data → train → stream → detect → recommend
- Chaos: Redis unavailability, malformed flows, missing columns
- Regression: benchmark report consistency across versions

## Extensibility Points

### Custom Anomaly Models

Implement `AnomalyDetectorInterface`:
```python
def fit(features):
    pass

def predict(features):  # Return -1 (anomaly) or 1 (normal)
    pass
```

### Custom Risk Propagation

Subclass `AttackGraph` and override `propagate_risk()`:
- Machine learning-based decay (learn from history)
- Privilege-aware propagation (higher score for privilege escalation targets)
- Time-varying thresholds (stricter during off-hours)

### Custom Policy Engines

Extend `PolicyEngine` to emit different action types:
- Packet rerouting via SDN
- Process termination via endpoint agents
- Network isolation via VLAN rules
- ML model retraining triggers

## Validation & Correctness

### Known Limitations

1. **Isolation Forest** requires manual contamination tuning—no automatic threshold
2. **Host Identity** falls back to port-based hashing (not ML-based entity linking)
3. **Graph assumes no false positives** in anomaly detection (would cause false risk propagation)
4. **Temporal decay** uses wall-clock time (not event time)—restart-safe

### Assumptions

- Flow data contains at least `src_ip`, `dst_ip`, or derivable host identifiers
- Anomalies are relatively rare (<30% of traffic)
- Network topology is relatively stable (graph size doesn't explode)

## Future Roadmap

**Phase 7: Persistence**
- Add SQLite/PostgreSQL for graph snapshots
- Enable temporal queries ("risk at time T")

**Phase 8: Explainability**
- Generate per-alert reports with evidence summary
- Visualize attack paths with Graphviz

**Phase 9: Closed-Loop**
- Integrate with SIEM (Splunk, ELK)
- Feedback loop: observed containment success → policy learning

**Phase 10: Distributed**
- Kafka instead of Redis for multi-DC
- Distributed graph processing (GraphX)
