# RAPIDS: Design Decisions & Rationale

## Why Isolation Forest for Anomaly Detection?

### Decision
Use unsupervised Isolation Forest instead of supervised classifiers (Random Forest, SVM).

### Rationale
1. **No Label Requirement**: Security data is expensive to label; unsupervised avoids this cost
2. **Novelty Detection**: Catches novel attacks not seen in training
3. **Scalability**: O(n log n) training, O(log n) inference per sample
4. **Curse of Dimensionality Resistant**: Works well in high-dim feature spaces
5. **Instance-Centric**: Doesn't model normal distribution; better for asymmetric distributions

### Trade-offs
| Aspect | Supervised | Unsupervised (IF) |
|--------|-----------|-----------------|
| Requires Labels | Yes | No |
| Time to Deploy | Months (data collection) | Days |
| Max Performance | 90%+ F1 (with good data) | 70-85% F1 |
| Novelty Detection | Limited | Strong |
| Interpretability | Per-feature importance | Per-isolation-path |

### Validation
- We provide Random Forest baseline to show supervised upper bound
- 5-fold CV demonstrates robustness across data partitions
- Threshold analysis shows F1 optimization is possible

---

## Why Attack Graph + Path Reasoning?

### Decision
Include graph-based risk reasoning and attack path computation.

### Rationale
1. **Explainability**: Path tells operator *how* attacker moves, not just *that* anomaly occurred
2. **Risk Quantification**: Combines anomaly severity with network topology
3. **Containment Targeting**: Path-aware policies block actual threats, not random traffic
4. **Lateral Movement Detection**: Propagation catches multi-step attacks

### Compared To
- **IoCs alone**: Only flag known-bad; miss novel attacks
- **ML alerts only**: No context on danger level or blast radius
- **Rules only**: Brittle; can't adapt to novel patterns

### Limitations & Mitigations
- **False Risk Propagation**: If anomaly detection has high FPR, graph gets polluted
  - Mitigation: Use contamination parameter to tune; rely on temporal decay to reset
- **Graph Explosions**: If every flow is anomalous, graph becomes fully connected
  - Mitigation: Threshold anomalies; aggressive decay; subnet-level graphs

---

## Why Temporal Decay?

### Decision
Implement exponential time-decay (24-hour half-life) for node and edge risk.

### Rationale
1. **Self-Healing**: Systems naturally recover from attacks if not re-compromised
2. **Reduces Alert Fatigue**: Old anomalies don't keep propagating forever
3. **Realistic Threat Model**: Intruders are transient; sustained compromise is rare
4. **Automatic Forgetfulness**: No need for manual "clear alert" operations

### Half-Life Choice (24 hours)
- Typical incident response window: 4–24 hours
- After 24h, risk drops to 50% (still flagged but lower priority)
- After 48h, risk drops to 25% (likely false alarm or remediated)

### Configuration
```yaml
reasoning:
  decay_half_life_hours: 24.0  # Tunable per environment
```

---

## Why Redis Streams vs Kafka?

### Decision
Use Redis Streams for this version; Kafka noted as future scale-out path.

### Rationale
**Redis Streams**:
- Simple, single-box deployment
- Built-in persistence (RDB/AOF)
- At-least-once semantics via consumer groups
- Sub-millisecond latency
- No reason to add Kafka complexity for Phase 1

**When to Upgrade to Kafka**:
- >10k flows/sec sustained load
- Multi-datacenter deployment
- Topic partitioning for parallelism
- Consumer lag monitoring across teams

---

## Why Batch Processing in Consumer?

### Decision
Batch flows before passing to anomaly detector (batch size 200).

### Rationale
1. **Hardware Efficiency**: GPUs/CPUs are faster on batches; less context-switching
2. **Latency-Throughput Tradeoff**: Batch tuning lets operators choose
3. **Simplicity**: No need for online learning / incremental updates
4. **Correctness**: Batch ensures model sees data in same format as training

### Tuning Guidance
```
Batch Size  | Throughput | Latency (p95)
50          | 500 fps    | 5ms
200         | 2000 fps   | 25ms (default)
1000        | 3000 fps   | 100ms
```

---

## Why Role-based Risk Propagation?

### Decision
Prioritize paths to high-value hosts (databases > servers > workstations).

### Rationale
1. **Business Context**: Database compromise is worse than workstation
2. **Attack Realism**: Attackers target data stores; workstations are means, not ends
3. **Output Quality**: Recommendations focus on high-impact targets

### Port-Based Role Inference
- **Limitation**: Works for standard deployments; breaks with custom ports
- **Future**: ML-based entity linking to infer roles from behavior

---

## Why Conservative Risk Reduction Estimates?

### Decision
Risk reduction `min(0.9, 0.2 + 0.5*risk)` caps at 90%.

### Rationale
1. **Realism**: Even perfect containment may not stop persistent attackers
2. **Accountability**: Don't over-promise mitigation
3. **Safety**: Operator still monitors even after containment
4. **Conservatism**: Better to under-estimate than over-estimate

### Example
- High-risk path (0.9): Estimated reduction = 0.2 + 0.45 = 65%
- Low-risk path (0.2): Estimated reduction = 0.2 + 0.1 = 30%

---

## Testing & Validation Approach

### Unit Tests
- **Isolation**: Test components independently (graph, detection, paths)
- **Determinism**: Fixed seeds for reproducible assertions
- **Edge Cases**: Empty graphs, single-node, cycles in path

### Cross-Validation
- **Goal**: Demonstrate model robustness, not optimize hyperparameters
- **Method**: 5-fold stratified CV (respect class imbalance)
- **Reporting**: Mean ± std for each metric

### Baselines
- **Supervised (RF)**: Shows upper bound with labels (not available in practice)
- **Naive (IF default)**: Shows impact of contamination tuning
- **Threshold Sweep**: Finds operating point (precision vs recall)

---

## Error Handling & Resilience

### Design Principles
1. **Fail Open**: On Redis error, log and continue (don't crash consumer)
2. **Retry with Backoff**: Connect failures use exponential backoff
3. **Data Validation**: Type hints + runtime checks for malformed flows
4. **Graceful Degradation**: If roles can't be inferred, default to workstation

### Not Implemented (Recommended for Production)
- Model versioning (reload without restart)
- Circuit breaker for failing anomaly detector
- Dead-letter queue for unparseable flows
- Metrics export (Prometheus)

---

## Comparison to Related Systems

| System | Detection | Reasoning | Streaming | Notes |
|--------|-----------|-----------|-----------|-------|
| RAPIDS | IF (unsupervised) | Graph + paths | Redis | Academic; extensible |
| Zeek | Rules + ML | Alert only | Native | Most mature IDS |
| Suricata | Rules + ML | Alert only | Syslog | Fast rule engine |
| OSQuery | Polling | Host-centric | Client | EPP; not flow-based |
| Weaveworks | ML (clustering) | None | Kubernetes | Cloud-native focus |

RAPIDS differentiator: **Graph reasoning without supervised labels**
