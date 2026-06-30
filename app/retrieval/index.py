"""Command entry point for Phase 1 indexing."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from app.config import DEFAULT_CONFIG_PATH, load_settings
from app.retrieval.pipeline import run_indexing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the Prisma sample corpus vector index.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to TOML config file.",
    )
    parser.add_argument("--corpus-path", help="Override configured corpus path.")
    parser.add_argument("--index-path", help="Override configured vector index path.")
    parser.add_argument("--manifest-path", help="Override configured manifest path.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild the index even if it is current.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = load_settings(Path(args.config)).with_overrides(
            corpus_path=args.corpus_path,
            index_path=args.index_path,
            manifest_path=args.manifest_path,
        )
        result = run_indexing(settings, force=bool(args.force))
    except Exception as exc:
        print(f"Indexing failed: {exc}", file=sys.stderr)
        return 1

    status = "index up to date" if result.up_to_date else "index rebuilt"
    print(f"Prisma indexing complete: {status}")
    print(f"documents={result.document_count}")
    print(f"chunks={result.chunk_count}")
    print(f"collection={result.collection_name}")
    print(f"index_path={result.index_path}")
    print(f"manifest_path={result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
