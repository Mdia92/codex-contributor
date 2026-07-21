from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from ..models import EngineeringReview, RepositoryMap
from ..env import load_local_environment
from .cache import cached_call


class ResponsesClient(Protocol):
    class responses:
        @staticmethod
        def create(**kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class FileChange:
    path: str
    change: str


@dataclass(frozen=True)
class ImplementationPlan:
    rationale: str
    files: tuple[FileChange, ...]
    tests: tuple[str, ...]


@dataclass(frozen=True)
class PlanResult:
    state: Literal["completed", "no_api_key_configured", "invalid_model_response"]
    plan: ImplementationPlan | None = None
    cache_hit: bool = False
    message: str = ""


PLAN_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["rationale", "files", "tests"],
    "properties": {
        "rationale": {"type": "string"},
        "files": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["path", "change"], "properties": {"path": {"type": "string"}, "change": {"type": "string"}}}},
        "tests": {"type": "array", "items": {"type": "string"}},
    },
}


def _prompt(review: EngineeringReview) -> str:
    evidence = "\n".join(f"- {item.citation}: {item.claim}" for item in review.evidence)
    return f"Engineering Review:\n{review.summary}\nFinding: {review.finding}\nRecommended Change: {review.recommended_change}\nEvidence:\n{evidence}\n\nProduce only a structured implementation plan. Touch the smallest safe set of files and include tests."


def plan(
    review: EngineeringReview,
    repository: RepositoryMap,
    *,
    client: ResponsesClient | None = None,
    cache_dir: Path = Path(".codex-contributor/cache"),
) -> PlanResult:
    load_local_environment()
    if not os.getenv("OPENAI_API_KEY"):
        return PlanResult("no_api_key_configured", message="No API key configured; implementation planning was not attempted.")
    prompt = _prompt(review)
    identity = f"planner:{review.issue.number}:{hashlib.sha256(prompt.encode()).hexdigest()}"

    def call() -> dict:
        actual = client
        if actual is None:
            from openai import OpenAI
            actual = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = actual.responses.create(
            model="gpt-5.6-sol", reasoning={"effort": "medium"},
            instructions="Create a minimal implementation plan grounded in the Engineering Review.",
            input=prompt,
            text={"format": {"type": "json_schema", "name": "implementation_plan", "strict": True, "schema": PLAN_SCHEMA}},
        )
        return {"output_text": response.output_text}

    raw, hit, _ = cached_call(repository, identity, cache_dir, call)
    try:
        data = json.loads(raw["output_text"])
        plan_value = ImplementationPlan(
            rationale=str(data["rationale"]),
            files=tuple(FileChange(str(item["path"]), str(item["change"])) for item in data["files"]),
            tests=tuple(str(item) for item in data["tests"]),
        )
        if not plan_value.files:
            raise ValueError("implementation plan contains no files")
        return PlanResult("completed", plan_value, hit)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return PlanResult("invalid_model_response", cache_hit=hit, message=f"Invalid implementation plan: {exc}")
