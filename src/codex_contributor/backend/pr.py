from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..engineering_review import render_markdown
from ..github_client import GitHubClient, GitHubError
from ..models import EngineeringReview
from .planner import ImplementationPlan
from .validation import ValidationResult


@dataclass(frozen=True)
class PRResult:
    state: str
    title: str
    body: str
    draft_path: Path | None = None
    url: str | None = None
    message: str = ""


def build_pr(review: EngineeringReview, plan: ImplementationPlan, validation: ValidationResult) -> tuple[str, str]:
    title = f"fix: {review.recommended_change[:70].rstrip('.') or 'evidence-backed issue change'}"
    body = f"""{render_markdown(review)}

## Implementation Plan

{plan.rationale}

""" + "\n".join(f"- `{change.path}` — {change.change}" for change in plan.files) + f"\n\nTests to add/run: {', '.join(plan.tests) or 'none specified'}\n\n## Validation Summary\n\n{validation.summary}\n"
    if validation.failures:
        body += "\n### Tests not fully passing\n\n" + "\n\n".join(validation.failures) + "\n"
    return title, body


def generate_pr(
    review: EngineeringReview,
    plan: ImplementationPlan,
    validation: ValidationResult,
    *,
    output_dir: Path = Path(".codex-contributor"),
    github: GitHubClient | None = None,
    head: str | None = None,
    base: str = "main",
    working_copy: Path | None = None,
) -> PRResult:
    title, body = build_pr(review, plan, validation)
    token = os.getenv("GITHUB_TOKEN")
    if token and github and working_copy:
        try:
            branch = "codex-contributor/issue-" + str(review.issue.number)
            files = {}
            for item in plan.files:
                path = (working_copy / item.path).resolve()
                if working_copy.resolve() not in path.parents:
                    raise GitHubError(f"refusing to publish path outside working copy: {item.path}")
                files[item.path] = path.read_text(encoding="utf-8")
            head = github.publish_branch(review.issue.owner, review.issue.repo, branch, files, base)
            url = github.create_pull_request(review.issue.owner, review.issue.repo, title, head, base, body)
            return PRResult("opened", title, body, url=url, message="Pull request opened.")
        except GitHubError as exc:
            message = f"Could not open pull request; saved a draft instead: {exc}"
    else:
        message = "GITHUB_TOKEN/working copy not configured; saved a local draft."
    output_dir.mkdir(parents=True, exist_ok=True)
    draft = output_dir / "draft-pr.md"
    draft.write_text(f"# {title}\n\n{body}", encoding="utf-8")
    return PRResult("draft", title, body, draft_path=draft, message=message)
