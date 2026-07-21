from pathlib import Path

from codex_contributor.models import Issue
from codex_contributor.pipeline import run_intake


class FakeGitHubClient:
    def get_issue(self, owner, repo, number):
        return Issue(owner, repo, number, "Document cache behavior", "Add caching", ("enhancement",), f"https://github.com/{owner}/{repo}/issues/{number}")

    def clone(self, repo_url, destination, depth=1):
        destination.mkdir(parents=True)
        (destination / "app.py").write_text("def cached():\n    return True\n", encoding="utf-8")
        return destination


def test_batch_one_intake_produces_honest_stub_review(tmp_path: Path):
    result = run_intake(
        "https://github.com/acme/demo",
        "https://github.com/acme/demo/issues/7",
        tmp_path,
        FakeGitHubClient(),
    )
    assert result.review.status == "human_review_required"
    assert result.review.metrics["files_explored"] == 1
    assert "# Engineering Review" in result.markdown
    assert "evidence-based model investigation has not run" in result.markdown

