from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from ..models import EngineeringReview, Issue, RepositoryMap
from ..env import load_local_environment


MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "medium"
INPUT_PRICE_PER_MILLION = 5.00
OUTPUT_PRICE_PER_MILLION = 30.00
CACHE_DIR = Path(".codex-contributor/cache")


class ResponsesClient(Protocol):
    class responses:
        @staticmethod
        def create(**kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class InvestigationResult:
    state: Literal["completed", "no_api_key_configured", "invalid_model_response"]
    review: EngineeringReview | None = None
    cache_hit: bool = False
    cache_path: Path | None = None
    message: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "summary", "evidence", "finding", "recommended_change", "confidence", "proceed"],
    "properties": {
        "status": {"type": "string", "enum": ["issue_confirmed", "issue_challenged", "human_review_required"]},
        "summary": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "claim", "start_line", "end_line", "symbol"],
                "properties": {
                    "path": {"type": "string"}, "claim": {"type": "string"},
                    "start_line": {"type": ["integer", "null"]}, "end_line": {"type": ["integer", "null"]},
                    "symbol": {"type": ["string", "null"]},
                },
            },
        },
        "finding": {"type": "string"},
        "recommended_change": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "proceed": {"type": "boolean"},
    },
}


SYSTEM_PROMPT = """You are the investigation stage of Codex Contributor. Treat the GitHub issue as a hypothesis and compare it against only the supplied repository evidence.

Return one Engineering Review with exactly these seven user-visible sections: Issue, Summary, Evidence, Finding, Recommended Change, Confidence, Proceed.

HARD EVIDENCE RULE:
- Every Evidence bullet MUST cite a specific repository file path.
- Cite a line range or symbol whenever the supplied context supports one.
- Never make an uncited codebase claim anywhere in the review.
- If a claim cannot be supported by a supplied file-level citation, refuse that claim and write "insufficient evidence" instead.
- Never invent paths, symbols, line numbers, behavior, test results, or implementation details.

Choose issue_confirmed when evidence supports the requested direction, issue_challenged when evidence supports a different recommendation, and human_review_required when evidence is insufficient. Proceed must be false whenever confidence is too low or evidence is insufficient."""


def _commit_sha(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def _ranked_context(issue: Issue, repository: RepositoryMap, max_files: int = 40, max_chars: int = 80_000) -> str:
    terms = {word.lower() for word in f"{issue.title} {issue.body}".replace("_", " ").split() if len(word) >= 4}
    ranked = sorted(repository.files, key=lambda path: (-sum(term in path.lower() for term in terms), path))
    root = Path(repository.root)
    sections: list[str] = []
    used = 0
    for relative in ranked:
        if len(sections) >= max_files or used >= max_chars:
            break
        path = root / relative
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not content.strip() or "\x00" in content:
            continue
        numbered = "\n".join(f"{number}: {line}" for number, line in enumerate(content.splitlines(), 1))
        block = f"\n--- FILE: {relative} ---\n{numbered[:max_chars - used]}"
        sections.append(block)
        used += len(block)
    return "".join(sections)


def _prompt(issue: Issue, repository: RepositoryMap) -> str:
    return f"""ISSUE
Repository: {issue.owner}/{issue.repo}
Number: {issue.number}
Title: {issue.title}
Labels: {', '.join(issue.labels) or 'none'}
Body:\n{issue.body or '(empty)'}

REPOSITORY MAP
Files mapped: {len(repository.files)}
Languages: {json.dumps(repository.languages, sort_keys=True)}
Detected test command: {json.dumps(repository.test_command)}

REPOSITORY EVIDENCE (line-numbered excerpts)
{_ranked_context(issue, repository)}
"""


def _cache_path(repository: RepositoryMap, issue: Issue, prompt: str, cache_dir: Path) -> Path:
    prompt_hash = hashlib.sha256((SYSTEM_PROMPT + "\n" + prompt).encode()).hexdigest()
    identity = f"{_commit_sha(Path(repository.root))}:{issue.number}:{MODEL}:{prompt_hash}"
    return cache_dir / f"{hashlib.sha256(identity.encode()).hexdigest()}.json"


def _usage(response: Any) -> tuple[int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0
    if isinstance(usage, dict):
        return int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0))
    return int(getattr(usage, "input_tokens", 0)), int(getattr(usage, "output_tokens", 0))


def _cost(input_tokens: int, output_tokens: int) -> float:
    return input_tokens / 1_000_000 * INPUT_PRICE_PER_MILLION + output_tokens / 1_000_000 * OUTPUT_PRICE_PER_MILLION


def _print_usage(input_tokens: int, output_tokens: int, cost: float, cache_hit: bool = False) -> None:
    source = "local cache" if cache_hit else MODEL
    print(f"Investigation usage ({source}): input={input_tokens:,} output={output_tokens:,} estimated_cost=${cost:.6f}")


def investigate(
    issue: Issue,
    repository: RepositoryMap,
    *,
    client: ResponsesClient | None = None,
    cache_dir: Path = CACHE_DIR,
) -> InvestigationResult:
    load_local_environment()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return InvestigationResult(
            state="no_api_key_configured",
            message="No API key configured. Set OPENAI_API_KEY to enable live investigation; no API call was attempted.",
        )

    user_prompt = _prompt(issue, repository)
    path = _cache_path(repository, issue, user_prompt, cache_dir)
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        input_tokens = int(cached.get("input_tokens", 0))
        output_tokens = int(cached.get("output_tokens", 0))
        cost = float(cached.get("estimated_cost_usd", 0.0))
        _print_usage(input_tokens, output_tokens, cost, cache_hit=True)
        try:
            data = json.loads(cached["output_text"])
            review = EngineeringReview.from_model_dict(issue, data, repository)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return InvestigationResult("invalid_model_response", cache_hit=True, cache_path=path, message=f"Cached Engineering Review is invalid: {exc}", input_tokens=input_tokens, output_tokens=output_tokens, estimated_cost_usd=cost)
        return InvestigationResult("completed", review, True, path, "Loaded cached investigation.", input_tokens, output_tokens, cost)

    if client is None:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": REASONING_EFFORT},
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
        text={"format": {"type": "json_schema", "name": "engineering_review", "strict": True, "schema": REVIEW_SCHEMA}},
    )
    input_tokens, output_tokens = _usage(response)
    estimated_cost = _cost(input_tokens, output_tokens)
    _print_usage(input_tokens, output_tokens, estimated_cost)
    output_text = getattr(response, "output_text", "")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "model": MODEL,
        "commit_sha": _commit_sha(Path(repository.root)),
        "issue_number": issue.number,
        "prompt_sha256": hashlib.sha256((SYSTEM_PROMPT + "\n" + user_prompt).encode()).hexdigest(),
        "output_text": output_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimated_cost,
    }, indent=2), encoding="utf-8")
    try:
        data = json.loads(output_text)
        review = EngineeringReview.from_model_dict(issue, data, repository)
    except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return InvestigationResult(state="invalid_model_response", cache_path=path, message=f"Invalid Engineering Review: {exc}", input_tokens=input_tokens, output_tokens=output_tokens, estimated_cost_usd=estimated_cost)
    return InvestigationResult("completed", review, False, path, "Live investigation completed.", input_tokens, output_tokens, estimated_cost)
