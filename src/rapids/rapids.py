import argparse

from rapids.cli import main as cli_main


def main():
    parser = argparse.ArgumentParser(description="RAPIDS entrypoint")
    parser.add_argument("--mode", choices=["offline", "streaming", "benchmark"], help="Run mode")
    args, _ = parser.parse_known_args()

    if args.mode == "streaming":
        cli_main_args = ["stream"]
    elif args.mode == "benchmark":
        cli_main_args = ["benchmark"]
    elif args.mode == "offline":
        cli_main_args = ["offline"]
    else:
        cli_main_args = []

    import sys

    sys.argv = [sys.argv[0]] + cli_main_args
    cli_main()


if __name__ == "__main__":
    main()
