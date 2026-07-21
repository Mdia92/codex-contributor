from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from codex_contributor.backend.investigation import investigate
from codex_contributor.engineering_review import render_markdown
from codex_contributor.models import EngineeringReview, Issue, RepositoryMap


VALID_REVIEW = {
    "status": "issue_challenged",
    "summary": "Caching exists, but invalidation evidence is missing.",
    "evidence": [{
        "path": "src/cache.py",
        "claim": "The cache decorator is already implemented.",
        "start_line": 1,
        "end_line": 2,
        "symbol": "cached",
    }],
    "finding": "The requested caching layer already exists.",
    "recommended_change": "Investigate invalidation after writes.",
    "confidence": 0.91,
    "proceed": True,
}


class MockResponses:
    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        assert kwargs["model"] == "gpt-5.6-sol"
        assert kwargs["reasoning"] == {"effort": "medium"}
        assert "Every Evidence bullet MUST cite" in kwargs["instructions"]
        return SimpleNamespace(
            output_text=json.dumps(VALID_REVIEW),
            usage=SimpleNamespace(input_tokens=1_000, output_tokens=200),
        )


class MockClient:
    def __init__(self):
        self.responses = MockResponses()


def fixture_data(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "cache.py").write_text("def cached(fn):\n    return fn\n", encoding="utf-8")
    issue = Issue("acme", "demo", 7, "Add caching", "Cache user reads", url="https://github.com/acme/demo/issues/7")
    repository = RepositoryMap(str(tmp_path), ["src/cache.py"], {"Python": 1}, ["python", "-m", "pytest"], {"src/cache.py": ["cached"]})
    return issue, repository


def test_cache_written_on_first_call_and_hit_on_second(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-live")
    issue, repository = fixture_data(tmp_path)
    client = MockClient()
    cache_dir = tmp_path / "cache"

    first = investigate(issue, repository, client=client, cache_dir=cache_dir)
    second = investigate(issue, repository, client=client, cache_dir=cache_dir)

    assert first.state == "completed" and first.cache_hit is False
    assert first.cache_path and first.cache_path.exists()
    assert second.state == "completed" and second.cache_hit is True
    assert client.responses.calls == 1
    assert "estimated_cost=$0.011000" in capsys.readouterr().out


def test_missing_api_key_never_calls_model(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    issue, repository = fixture_data(tmp_path)
    client = MockClient()

    result = investigate(issue, repository, client=client, cache_dir=tmp_path / "cache")

    assert result.state == "no_api_key_configured"
    assert "No API key configured" in result.message
    assert client.responses.calls == 0


def test_engineering_review_schema_validates_citations(tmp_path):
    issue, repository = fixture_data(tmp_path)
    review = EngineeringReview.from_model_dict(issue, VALID_REVIEW, repository)
    assert review.confidence == pytest.approx(0.91)
    assert review.evidence[0].citation == "src/cache.py:L1-L2"

    invalid = {**VALID_REVIEW, "evidence": [{**VALID_REVIEW["evidence"][0], "path": "invented.py"}]}
    with pytest.raises(ValueError, match="outside the repository map"):
        EngineeringReview.from_model_dict(issue, invalid, repository)


def test_rendered_review_has_exact_seven_sections(tmp_path):
    issue, repository = fixture_data(tmp_path)
    markdown = render_markdown(EngineeringReview.from_model_dict(issue, VALID_REVIEW, repository))
    headings = [line for line in markdown.splitlines() if line.startswith("## ")]
    assert headings == [
        "## Issue", "## Summary", "## Evidence", "## Finding",
        "## Recommended Change", "## Confidence", "## Proceed",
    ]
