from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time

from ..engineering_review import render_markdown
from ..github_client import GitHubClient
from ..issue_parser import parse_repo_url
from ..models import EngineeringReview, RepositoryMap
from ..repo_explorer import map_repository
from .investigation import InvestigationResult, investigate
from .planner import PlanResult, plan
from .pr import PRResult, generate_pr
from .validation import ValidationResult, validate
from .writer import WriteResult, write_plan


@dataclass(frozen=True)
class PipelineResult:
    state: str
    review: InvestigationResult
    plan: PlanResult | None = None
    writer: WriteResult | None = None
    validation: ValidationResult | None = None
    pr: PRResult | None = None
    review_path: Path | None = None
    message: str = ""


def run_pipeline(
    repo_url: str,
    issue_number: int,
    *,
    workspace: Path,
    client: GitHubClient | None = None,
    model_client=None,
    cache_dir: Path = Path(".codex-contributor/cache"),
) -> PipelineResult:
    workspace.mkdir(parents=True, exist_ok=True)
    trace: list[dict[str, object]] = []

    def record(stage: str, started: float, decision: str) -> None:
        trace.append({"stage": stage, "duration_ms": round((time.perf_counter() - started) * 1000), "decision": decision})

    def persist_trace() -> None:
        (workspace / "execution-trace.json").write_text(json.dumps({"stages": trace}, indent=2), encoding="utf-8")

    github = client or GitHubClient()
    owner, repo = parse_repo_url(repo_url)
    issue = github.get_issue(owner, repo, issue_number)
    clone_path = workspace / repo
    if not clone_path.exists():
        github.clone(repo_url, clone_path)
    repository = map_repository(clone_path)
    started = time.perf_counter()
    review_result = investigate(issue, repository, client=model_client, cache_dir=cache_dir)
    record("Investigation Agent", started, review_result.state)
    review_path = workspace / "engineering-review.md"
    (workspace / "issue.json").write_text(json.dumps({
        "owner": issue.owner, "repo": issue.repo, "number": issue.number,
        "title": issue.title, "body": issue.body, "labels": list(issue.labels), "url": issue.url,
    }, indent=2), encoding="utf-8")
    if review_result.review:
        review_path.write_text(render_markdown(review_result.review), encoding="utf-8")
    if review_result.state != "completed":
        persist_trace()
        return PipelineResult(review_result.state, review_result, review_path=review_path, message=review_result.message)
    if review_result.review.confidence < 0.5:
        review_path.write_text(
            review_path.read_text(encoding="utf-8")
            + "\n## Human Review Required\n\nImplementation is halted because investigation confidence is below 0.50.\n",
            encoding="utf-8",
        )
        trace.append({"stage": "Confidence Gate", "duration_ms": 0, "decision": "halted: confidence below 0.50"})
        persist_trace()
        return PipelineResult("halted_confidence_gate", review_result, review_path=review_path, message="Human Review Required: confidence is below the 0.50 implementation threshold.")
    started = time.perf_counter()
    plan_result = plan(review_result.review, repository, client=model_client, cache_dir=cache_dir)
    record("Implementation Agent — plan", started, plan_result.state)
    if plan_result.state != "completed":
        persist_trace()
        return PipelineResult(plan_result.state, review_result, plan_result, review_path=review_path, message=plan_result.message)
    (workspace / "plan.json").write_text(json.dumps({
        "rationale": plan_result.plan.rationale,
        "files": [{"path": item.path, "change": item.change} for item in plan_result.plan.files],
        "tests": list(plan_result.plan.tests),
    }, indent=2), encoding="utf-8")
    started = time.perf_counter()
    writer_result = write_plan(plan_result.plan, repository, client=model_client, cache_dir=cache_dir)
    record("Implementation Agent — write", started, writer_result.state)
    if writer_result.state != "completed":
        persist_trace()
        return PipelineResult(writer_result.state, review_result, plan_result, writer_result, review_path=review_path, message=writer_result.message)
    started = time.perf_counter()
    validation_result = validate(repository, client=model_client, cache_dir=cache_dir)
    record("Validation Agent", started, validation_result.state)
    (workspace / "validation.json").write_text(json.dumps({
        "state": validation_result.state, "iterations": validation_result.iterations,
        "summary": validation_result.summary, "failures": list(validation_result.failures),
    }, indent=2), encoding="utf-8")
    started = time.perf_counter()
    pr_result = generate_pr(review_result.review, plan_result.plan, validation_result, output_dir=workspace / ".codex-contributor", github=github, working_copy=clone_path)
    record("Pull-request handoff", started, pr_result.state)
    (workspace / "pr.json").write_text(json.dumps({
        "state": pr_result.state, "title": pr_result.title, "url": pr_result.url,
        "message": pr_result.message, "draft_path": str(pr_result.draft_path) if pr_result.draft_path else None,
    }, indent=2), encoding="utf-8")
    persist_trace()
    return PipelineResult("completed", review_result, plan_result, writer_result, validation_result, pr_result, review_path, "Pipeline completed.")
