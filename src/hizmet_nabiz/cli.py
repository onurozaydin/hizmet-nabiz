"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hizmet_nabiz.config import load_settings
from hizmet_nabiz.extract import ExtractionError, extract_dataset
from hizmet_nabiz.logging_utils import configure_logging
from hizmet_nabiz.pipeline import build_analysis


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hizmet-nabiz",
        description="Build decision-grade NYC 311 service intelligence artifacts.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/analysis.yml"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    fetch = subparsers.add_parser("fetch", help="Download the fixed official-data snapshot")
    fetch.add_argument("--output", type=Path, default=Path("data/raw/requests.csv.gz"))
    fetch.add_argument("--manifest", type=Path, default=Path("data/raw/manifest.json"))
    build = subparsers.add_parser("build", help="Validate and build analytics artifacts")
    build.add_argument("--input", type=Path, default=Path("data/raw/requests.csv.gz"))
    build.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    build.add_argument("--dashboard", type=Path, default=Path("dashboard/index.html"))
    all_command = subparsers.add_parser("all", help="Fetch, validate, analyze, and render")
    all_command.add_argument("--input", type=Path, default=Path("data/raw/requests.csv.gz"))
    all_command.add_argument("--manifest", type=Path, default=Path("data/raw/manifest.json"))
    all_command.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    all_command.add_argument("--dashboard", type=Path, default=Path("dashboard/index.html"))
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = _parser().parse_args(argv)
    settings = load_settings(args.config)
    try:
        if args.command == "fetch":
            extract_dataset(settings.source, args.output, args.manifest)
        elif args.command == "build":
            build_analysis(args.input, settings, args.output_dir, args.dashboard)
        else:
            extract_dataset(settings.source, args.input, args.manifest)
            build_analysis(args.input, settings, args.output_dir, args.dashboard)
    except (ExtractionError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
