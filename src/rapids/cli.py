import argparse

from rapids.core.config_loader import load_config
from rapids.core.logger import setup_logger, log_event
from rapids.evaluation.benchmarking import build_report
from rapids.streaming.run_streaming_ids import main as run_streaming
from rapids.main import main as run_offline


def run_benchmark(args):
    config = load_config()
    logger = setup_logger(config)
    report = build_report(args.dataset, args.max_rows, args.batch_size)
    log_event(logger, "benchmark.complete", rows=report["rows_used"])

    with open(args.output, "w") as f:
        import json

        json.dump(report, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="RAPIDS CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("offline", help="Run offline feature impact pipeline")
    subparsers.add_parser("stream", help="Run streaming IDS")

    bench = subparsers.add_parser("benchmark", help="Run Phase 6 benchmarks")
    bench.add_argument("--dataset", default="datasets/sample.csv")
    bench.add_argument("--max-rows", type=int, default=5000)
    bench.add_argument("--batch-size", type=int, default=256)
    bench.add_argument("--output", default="evaluation/benchmark_report.json")

    args = parser.parse_args()

    if args.command == "offline":
        run_offline()
    elif args.command == "stream":
        run_streaming()
    elif args.command == "benchmark":
        run_benchmark(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
