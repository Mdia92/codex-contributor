from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from codex_contributor.backend.pipeline import run_pipeline
from codex_contributor.backend.planner import ImplementationPlan, FileChange, plan
from codex_contributor.backend.pr import generate_pr
from codex_contributor.backend.validation import validate
from codex_contributor.backend.writer import write_plan
from codex_contributor.models import EngineeringReview, Evidence, Issue, RepositoryMap


class ResponseClient:
    def __init__(self, payloads):
        self.payloads = iter(payloads)
        self.calls = 0
        self.responses = self

    def create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(output_text=json.dumps(next(self.payloads)))


def review_and_map(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("def run():\n    return 'old'\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    issue = Issue("acme", "demo", 1, "Change run", "Change the run behavior", url="https://github.com/acme/demo/issues/1")
    repo = RepositoryMap(str(tmp_path), ["src/app.py", "pyproject.toml"], {"Python": 1}, ["python", "-m", "pytest"], {"src/app.py": ["run"]})
    review = EngineeringReview(issue, "issue_confirmed", "confirmed", [Evidence("src/app.py", "run exists", 1, 2, "run")], "change is scoped", "update run", .9, "proceed")
    return issue, repo, review


def test_planner_cache_and_writer_one_call_per_file(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    _, repo, review = review_and_map(tmp_path)
    plan_client = ResponseClient([{"rationale": "small change", "files": [{"path": "src/app.py", "change": "update run"}], "tests": ["tests/test_app.py"]}])
    first = plan(review, repo, client=plan_client, cache_dir=tmp_path / "cache")
    second = plan(review, repo, client=plan_client, cache_dir=tmp_path / "cache")
    assert first.state == second.state == "completed"
    assert second.cache_hit is True and plan_client.calls == 1

    writer_client = ResponseClient([{"path": "src/app.py", "content": "def run():\n    return 'new'\n"}])
    result = write_plan(first.plan, repo, client=writer_client, cache_dir=tmp_path / "cache")
    assert result.state == "completed" and writer_client.calls == 1
    assert "new" in (tmp_path / "src/app.py").read_text(encoding="utf-8")


def test_validation_repairs_failure_and_caps_iterations(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    _, repo, _ = review_and_map(tmp_path)
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text("from src.app import run\ndef test_run():\n    assert run() == 'new'\n", encoding="utf-8")
    repair = {"summary": "updated app", "files": [{"path": "src/app.py", "content": "def run():\n    return 'new'\n"}]}
    result = validate(repo, client=ResponseClient([repair]), cache_dir=tmp_path / "cache")
    assert result.state == "passed" and result.iterations == 2


def test_pr_draft_embeds_review_first_and_validation_failure_section(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "")
    _, _, review = review_and_map(tmp_path)
    plan_value = ImplementationPlan("small", (FileChange("src/app.py", "update"),), ("pytest",))
    validation = SimpleNamespace(summary="Tests not fully passing after 5 validation iterations.", failures=("Iteration 5: failure",))
    result = generate_pr(review, plan_value, validation, output_dir=tmp_path / ".codex-contributor")
    assert result.state == "draft"
    content = result.draft_path.read_text(encoding="utf-8")
    assert content.index("# Engineering Review") < content.index("## Implementation Plan") < content.index("## Validation Summary")
    assert "Tests not fully passing" in content


def test_pr_publishing_uses_fork_branch_and_opens_pr(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "mock-token")
    _, _, review = review_and_map(tmp_path)
    plan_value = ImplementationPlan("small", (FileChange("src/app.py", "update"),), ("pytest",))
    validation = SimpleNamespace(summary="Tests passed.", failures=())

    class MockGitHub:
        def __init__(self):
            self.published = None
            self.opened = None

        def publish_branch(self, owner, repo, branch, files, base):
            self.published = (owner, repo, branch, files, base)
            return "Mdia92:codex-contributor/issue-1"

        def create_pull_request(self, owner, repo, title, head, base, body):
            self.opened = (owner, repo, title, head, base, body)
            return "https://github.com/acme/demo/pull/2"

    github = MockGitHub()
    result = __import__("codex_contributor.backend.pr", fromlist=["generate_pr"]).generate_pr(
        review, plan_value, validation, github=github, working_copy=tmp_path,
    )
    assert result.state == "opened"
    assert github.published[2] == "codex-contributor/issue-1"
    assert github.published[3]["src/app.py"].startswith("def run")
    assert github.opened[3] == "Mdia92:codex-contributor/issue-1"


def test_end_to_end_pipeline_uses_only_mocked_responses(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("GITHUB_TOKEN", "")

    class FakeGitHub:
        def get_issue(self, owner, repo, number):
            return Issue(owner, repo, number, "Change run", "Change the run behavior", url=f"https://github.com/{owner}/{repo}/issues/{number}")

        def clone(self, url, destination, depth=1):
            destination.mkdir(parents=True)
            (destination / "src").mkdir()
            (destination / "src/app.py").write_text("def run():\n    return 'old'\n", encoding="utf-8")
            (destination / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            (destination / "tests").mkdir()
            (destination / "tests/test_app.py").write_text("from src.app import run\ndef test_run():\n    assert run() == 'new'\n", encoding="utf-8")
            return destination

    class FullClient(ResponseClient):
        def __init__(self):
            self.calls = 0
            self.responses = self

        def create(self, **kwargs):
            self.calls += 1
            instructions = kwargs.get("instructions", "")
            if "Engineering Review" in instructions and "implementation plan" in instructions:
                payload = {"rationale": "small", "files": [{"path": "src/app.py", "change": "update"}], "tests": ["pytest"]}
            elif "complete source file" in instructions:
                payload = {"path": "src/app.py", "content": "def run():\n    return 'new'\n"}
            else:
                payload = {"status": "issue_confirmed", "summary": "confirmed", "evidence": [{"path": "src/app.py", "claim": "run exists", "start_line": 1, "end_line": 2, "symbol": "run"}], "finding": "scoped", "recommended_change": "update run", "confidence": .9, "proceed": True}
            return SimpleNamespace(output_text=json.dumps(payload), usage=SimpleNamespace(input_tokens=10, output_tokens=10))

    result = run_pipeline("https://github.com/acme/demo", 1, workspace=tmp_path / "work", client=FakeGitHub(), model_client=FullClient(), cache_dir=tmp_path / "cache")
    assert result.state == "completed"
    assert result.pr and result.pr.state == "draft"
    assert result.validation and result.validation.state == "passed"


def test_confidence_gate_halts_before_planning(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    class FakeGitHub:
        def get_issue(self, owner, repo, number):
            return Issue(owner, repo, number, "Unclear change", "Not enough context", url="https://github.com/acme/demo/issues/1")

        def clone(self, url, destination, depth=1):
            destination.mkdir(parents=True)
            (destination / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
            return destination

    class LowConfidence(ResponseClient):
        def __init__(self):
            self.calls = 0
            self.responses = self

        def create(self, **kwargs):
            self.calls += 1
            return SimpleNamespace(output_text=json.dumps({"status": "human_review_required", "summary": "unclear", "evidence": [], "finding": "insufficient evidence", "recommended_change": "ask maintainer", "confidence": .2, "proceed": False}))

    model = LowConfidence()
    result = run_pipeline("https://github.com/acme/demo", 1, workspace=tmp_path / "work", client=FakeGitHub(), model_client=model, cache_dir=tmp_path / "cache")
    assert result.state == "halted_confidence_gate"
    assert result.plan is None and model.calls == 1
    assert "Human Review Required" in result.review_path.read_text(encoding="utf-8")
