from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from ..repo_explorer import detect_test_command
from ..test_runner import TestResult, run_tests
from ..models import RepositoryMap
from .cache import cached_call


class ResponsesClient(Protocol):
    class responses:
        @staticmethod
        def create(**kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class ValidationResult:
    state: Literal["passed", "tests_not_fully_passing", "no_api_key_configured", "no_test_runner"]
    iterations: int
    summary: str
    failures: tuple[str, ...] = ()


PATCH_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["summary", "files"],
    "properties": {
        "summary": {"type": "string"},
        "files": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["path", "content"], "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}},
    },
}


def _apply(root: Path, path: str, content: str) -> None:
    destination = (root / path).resolve()
    if root not in destination.parents and destination != root:
        raise ValueError(f"validation patch escaped working copy: {path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def validate(
    repository: RepositoryMap,
    *,
    client: ResponsesClient | None = None,
    cache_dir: Path = Path(".codex-contributor/cache"),
    max_iterations: int = 5,
) -> ValidationResult:
    command = repository.test_command or detect_test_command(Path(repository.root))
    if not command:
        return ValidationResult("no_test_runner", 0, "No supported test framework detected.")
    failures: list[str] = []
    for iteration in range(1, max_iterations + 1):
        result: TestResult = run_tests(Path(repository.root), command)
        if result.passed:
            return ValidationResult("passed", iteration, f"Tests passed on validation iteration {iteration}.", tuple(failures))
        failure = (result.stdout + "\n" + result.stderr).strip()[-20_000:]
        failures.append(f"Iteration {iteration}: {failure}")
        if not os.getenv("OPENAI_API_KEY"):
            return ValidationResult("no_api_key_configured", iteration, "Tests failed, but no API key is configured for an automated repair iteration.", tuple(failures))
        prompt = f"Validation iteration {iteration} failed. Working copy: {repository.root}\nTest command: {command}\nFailure:\n{failure}\nReturn only complete replacement files needed to repair the failure. If no safe repair is supported, return an empty files list."
        identity = f"validation:{iteration}:{hashlib.sha256(prompt.encode()).hexdigest()}"

        def call(prompt=prompt) -> dict:
            actual = client
            if actual is None:
                from openai import OpenAI
                actual = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            response = actual.responses.create(
                model="gpt-5.6-sol", reasoning={"effort": "medium"},
                instructions="Repair only the observed test failure; do not invent passing results.",
                input=prompt,
                text={"format": {"type": "json_schema", "name": "validation_patch", "strict": True, "schema": PATCH_SCHEMA}},
            )
            return {"output_text": response.output_text}

        raw, _, _ = cached_call(repository, identity, cache_dir, call)
        try:
            patch = json.loads(raw["output_text"])
            for file in patch["files"]:
                _apply(Path(repository.root).resolve(), str(file["path"]), str(file["content"]))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"Iteration {iteration}: invalid repair response: {exc}")
    return ValidationResult("tests_not_fully_passing", max_iterations, f"Tests not fully passing after {max_iterations} validation iterations.", tuple(failures))

