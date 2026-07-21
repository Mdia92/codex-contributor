from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import run_intake
from .env import load_local_environment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-contributor", description="Investigate GitHub issues before writing code.")
    parser.add_argument("--repo", required=True, help="HTTPS GitHub repository URL")
    parser.add_argument("--issue", required=True, help="Full GitHub issue URL")
    parser.add_argument("--workspace", type=Path, help="Directory used for the cloned repository")
    parser.add_argument("--output", type=Path, default=Path("engineering-review.md"))
    return parser


def build_run_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-contributor run", description="Run the evidence-first contribution pipeline.")
    parser.add_argument("--repo", required=True, help="HTTPS GitHub repository URL")
    parser.add_argument("--issue", required=True, type=int, help="GitHub issue number")
    parser.add_argument("--workspace", type=Path, default=Path(".codex-contributor/work"))
    return parser


def build_export_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-contributor export-review", description="Export an Engineering Review to premium static HTML.")
    parser.add_argument("--input", required=True, type=Path, help="Engineering Review Markdown path")
    parser.add_argument("--output", required=True, type=Path, help="HTML output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_local_environment()
    # Windows may otherwise inherit a legacy code page that cannot render the
    # Engineering Review's status glyphs.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    argv = list(argv) if argv is not None else sys.argv[1:]
    if argv and argv[0] == "export-review":
        from .backend.html_export import export_review
        args = build_export_parser().parse_args(argv[1:])
        try:
            result = export_review(args.input, args.output)
            print(f"Exported Engineering Review to {result.resolve()}")
            return 0
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if argv and argv[0] == "run":
        from .backend.pipeline import run_pipeline
        args = build_run_parser().parse_args(argv[1:])
        try:
            result = run_pipeline(args.repo, args.issue, workspace=args.workspace)
            if result.review_path:
                print(f"Engineering Review: {result.review_path.resolve()}")
            print(result.message or result.state)
            if result.pr and result.pr.draft_path:
                print(f"PR draft: {result.pr.draft_path.resolve()}")
            return 0 if result.state in {"completed", "no_api_key_configured", "halted_confidence_gate"} else 2
        except (ValueError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
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
