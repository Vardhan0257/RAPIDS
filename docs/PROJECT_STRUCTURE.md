# Project Structure

## Directory Organization

```
rapids/
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI/CD pipeline
├── docs/
│   ├── ARCHITECTURE.md              # System design, scaling, deployment
│   ├── DESIGN_DECISIONS.md          # Algorithm rationale, tradeoffs
│   └── RESUME_VALUE.md              # Interview positioning, bullet points
├── src/rapids/
│   ├── __init__.py
│   ├── cli.py                       # CLI entry point (rapids command)
│   ├── main.py                      # Feature impact pipeline
│   ├── rapids.py                    # Main package initialization
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config_loader.py         # YAML config management
│   │   ├── logger.py                # Structured logging setup
│   │   └── redis_utils.py           # Redis connection with retry logic
│   ├── detection/
│   │   ├── __init__.py
│   │   ├── anomaly_model.py         # Isolation Forest training & evaluation
│   │   └── data_loader.py           # Data loading, preprocessing, validation
│   ├── reasoning/
│   │   ├── __init__.py
│   │   ├── attack_graph.py          # Attack graph with temporal decay
│   │   ├── attack_paths.py          # Path computation (BFS/DFS)
│   │   ├── engine.py                # Reasoning engine orchestration
│   │   ├── host_identity.py         # Host extraction from flows
│   │   ├── policy_engine.py         # Containment recommendations
│   │   └── role_classifier.py       # Port-based role inference
│   ├── streaming/
│   │   ├── __init__.py
│   │   ├── consumer.py              # Redis stream consumer
│   │   ├── producer.py              # Redis stream producer
│   │   └── run_streaming_ids.py     # Streaming IDS orchestration
│   └── evaluation/
│       ├── __init__.py
│       ├── benchmarking.py          # End-to-end benchmarking suite
│       ├── feature_analysis.py      # Feature impact experiments
│       ├── model_evaluation.py      # Cross-validation, baselines
│       └── phase_checks.py          # Phase validation checks
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures & configuration
│   ├── test_anomaly_model.py        # Detection module tests
│   ├── test_attack_graph_enhanced.py # Graph propagation & decay tests
│   ├── test_attack_paths.py         # Path computation tests
│   ├── test_host_identity.py        # Host extraction tests
│   ├── test_phase4_phase5.py        # Integration tests
│   └── test_reasoning_engine.py     # Reasoning engine tests
├── config/
│   └── config.yaml                  # YAML configuration (Redis, streaming, etc.)
├── datasets/
│   └── sample.csv                   # Sample network flow data (CIC-IDS2018)
├── .gitignore                       # Git ignore rules
├── LICENSE                          # MIT License
├── README.md                        # Main documentation
├── pyproject.toml                   # Python project metadata & dependencies
├── requirements.txt                 # pip-installable dependencies
└── requirements-dev.txt            # Development dependencies (testing, linting)
```

## Key Files

### Configuration
- **config/config.yaml** – Redis connection, streaming parameters, model hyperparameters
- **pyproject.toml** – Package metadata, entry points (`rapids` command), Python version

### Documentation
- **README.md** – Quick-start, features, usage examples
- **docs/ARCHITECTURE.md** – System design, complexity analysis, scaling patterns
- **docs/DESIGN_DECISIONS.md** – Algorithm justification, tradeoffs, future roadmap
- **docs/RESUME_VALUE.md** – Interview positioning, bullet points for FAANG

### Core Modules

#### Detection (`src/rapids/detection/`)
- **anomaly_model.py** – Isolation Forest training, cross-validation, threshold analysis
- **data_loader.py** – CSV loading, preprocessing, validation, scaling

#### Reasoning (`src/rapids/reasoning/`)
- **attack_graph.py** – Graph structure with temporal decay, risk propagation
- **attack_paths.py** – Path computation with risk combination
- **engine.py** – Orchestration of graph, paths, and policy
- **policy_engine.py** – Recommendation generation and containment simulation

#### Streaming (`src/rapids/streaming/`)
- **producer.py** – Read CSV → Redis Streams
- **consumer.py** – Batch inference, anomaly detection, risk propagation
- **run_streaming_ids.py** – Main streaming pipeline orchestration

#### Evaluation (`src/rapids/evaluation/`)
- **benchmarking.py** – Throughput, latency, metrics, baselines
- **model_evaluation.py** – Cross-validation, supervised baseline, threshold analysis
- **phase_checks.py** – Validation of graph, risk, paths, policy, and benchmarks

### Testing
- **conftest.py** – Pytest fixtures for reproducible test data
- **test_anomaly_model.py** – Detection pipeline tests
- **test_attack_graph_enhanced.py** – Graph propagation, temporal decay tests
- **test_reasoning_engine.py** – Multi-step anomaly handling tests
- **test_phase4_phase5.py** – Integration tests

## CI/CD & Dependencies

- **.github/workflows/ci.yml** – Multi-version testing (3.10, 3.11, 3.12), coverage, linting
- **pyproject.toml** – Defines `rapids` CLI command (entry point)
- **requirements.txt** – Production dependencies
- **requirements-dev.txt** – Development dependencies (pytest, black, mypy)

## Standards

- **Type Hints**: Full PEP 484 annotations on core modules
- **Testing**: >85% coverage via pytest
- **Linting**: Black (formatting), Pylint (style), mypy (type checking)
- **Logging**: Structured logging with event tracking
- **Error Handling**: Exponential backoff, data validation, graceful degradation
