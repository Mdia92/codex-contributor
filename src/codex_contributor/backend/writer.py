from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from ..models import RepositoryMap
from ..env import load_local_environment
from .cache import cached_call
from .planner import ImplementationPlan


class ResponsesClient(Protocol):
    class responses:
        @staticmethod
        def create(**kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class WriteResult:
    state: Literal["completed", "no_api_key_configured", "invalid_model_response", "unsafe_path"]
    files_written: tuple[str, ...] = ()
    message: str = ""


WRITER_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["path", "content"],
    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
}


def _safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"writer refused path outside working copy: {relative}")
    return candidate


def write_plan(
    plan: ImplementationPlan,
    repository: RepositoryMap,
    *,
    client: ResponsesClient | None = None,
    cache_dir: Path = Path(".codex-contributor/cache"),
) -> WriteResult:
    load_local_environment()
    if not os.getenv("OPENAI_API_KEY"):
        return WriteResult("no_api_key_configured", message="No API key configured; code writing was not attempted.")
    root = Path(repository.root).resolve()
    written: list[str] = []
    for change in plan.files:
        try:
            destination = _safe_path(root, change.path)
        except ValueError as exc:
            return WriteResult("unsafe_path", tuple(written), str(exc))
        prompt = f"File to implement: {change.path}\nRequested change: {change.change}\nPreserve project conventions. Return the complete file contents, not a diff."
        identity = f"writer:{change.path}:{hashlib.sha256((prompt + json.dumps(plan.tests)).encode()).hexdigest()}"

        def call(prompt=prompt) -> dict:
            actual = client
            if actual is None:
                from openai import OpenAI
                actual = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            response = actual.responses.create(
                model="gpt-5.6-sol", reasoning={"effort": "medium"},
                instructions="Write one complete source file for the requested implementation change.",
                input=prompt,
                text={"format": {"type": "json_schema", "name": "file_contents", "strict": True, "schema": WRITER_SCHEMA}},
            )
            return {"output_text": response.output_text}

        raw, _, _ = cached_call(repository, identity, cache_dir, call)
        try:
            data = json.loads(raw["output_text"])
            if data["path"] != change.path:
                raise ValueError("model returned a different path than requested")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(str(data["content"]), encoding="utf-8")
            written.append(change.path)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return WriteResult("invalid_model_response", tuple(written), f"Invalid writer response for {change.path}: {exc}")
    return WriteResult("completed", tuple(written))
