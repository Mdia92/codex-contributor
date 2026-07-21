from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import run_intake


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-contributor", description="Investigate GitHub issues before writing code.")
    parser.add_argument("--repo", required=True, help="HTTPS GitHub repository URL")
    parser.add_argument("--issue", required=True, help="Full GitHub issue URL")
    parser.add_argument("--workspace", type=Path, help="Directory used for the cloned repository")
    parser.add_argument("--output", type=Path, default=Path("engineering-review.md"))
    return parser


def main(argv: list[str] | None = None) -> int:
    # Windows may otherwise inherit a legacy code page that cannot render the
    # Engineering Review's status glyphs.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        result = run_intake(args.repo, args.issue, args.workspace)
        args.output.write_text(result.markdown, encoding="utf-8")
        print(result.markdown)
        print(f"\nSaved Engineering Review to {args.output.resolve()}")
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
