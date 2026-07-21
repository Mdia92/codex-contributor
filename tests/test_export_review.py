from pathlib import Path

from codex_contributor.backend.html_export import export_review


def test_export_review_creates_premium_static_document(tmp_path: Path):
    source = tmp_path / "review.md"
    output = tmp_path / "review.html"
    source.write_text("# Engineering Review\n\n## Evidence\n\n- `src/app.py:L1-L2` — **cited claim**\n", encoding="utf-8")
    export_review(source, output)
    html = output.read_text(encoding="utf-8")
    assert "Codex Contributor" in html
    assert "section-card" in html
    assert "src/app.py:L1-L2" in html
    assert "cited claim" in html

