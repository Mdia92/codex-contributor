from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".codex-contributor"
OUTPUT_DIR = Path(st.sidebar.text_input("Output directory", str(DEFAULT_OUTPUT))).expanduser()


def _candidate_dirs() -> list[Path]:
    return [
        OUTPUT_DIR,
        DEFAULT_OUTPUT / "work" / ".codex-contributor",
        DEFAULT_OUTPUT / "work",
    ]


def _find(output_name: str) -> Path | None:
    for directory in _candidate_dirs():
        candidate = directory / output_name
        if candidate.exists():
            return candidate
    return None


def _read_text(name: str, fallback: str = "") -> str:
    path = _find(name)
    return path.read_text(encoding="utf-8", errors="replace") if path else fallback


def _read_json(name: str) -> dict[str, Any]:
    path = _find(name)
    if not path:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _review_fields(markdown: str) -> dict[str, str]:
    result: dict[str, str] = {}
    headings = list(re.finditer(r"^## (.+)$", markdown, re.MULTILINE))
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        result[match.group(1).strip()] = markdown[match.end():end].strip()
    return result


def _status(markdown: str) -> str:
    if "Issue Challenged" in markdown:
        return "⚠ Issue Challenged"
    if "Human Review Required" in markdown or "human_review_required" in markdown:
        return "Human Review Required"
    if "Issue Confirmed" in markdown:
        return "✓ Issue Confirmed"
    return "Investigation pending"


def _confidence(markdown: str) -> str:
    match = re.search(r"## Confidence\s+([0-9]+%)", markdown)
    return match.group(1) if match else "—"


st.set_page_config(page_title="Codex Contributor", page_icon="✦", layout="wide")
st.markdown("""
<style>
    .stApp { background: #f5f7fb; color: #172033; }
    .hero { background: linear-gradient(135deg,#111827 0%,#243b64 100%); color:#fff; padding:2.2rem 2.4rem; border-radius:18px; margin-bottom:1.2rem; }
    .hero h1 { font-size:2.25rem; margin:0 0 .35rem 0; }
    .hero p { color:#c9d6ef; margin:0; font-size:1.05rem; }
    .review-card { background:#fff; border:1px solid #dfe6f2; border-radius:16px; padding:1.6rem 1.8rem; box-shadow:0 8px 24px rgba(33,55,90,.08); }
    .badge { display:inline-block; padding:.45rem .8rem; border-radius:999px; background:#e8eefc; color:#244b9b; font-weight:700; }
    .confidence { font-size:3.2rem; font-weight:800; color:#1f4fa3; line-height:1; }
    .eyebrow { color:#64748b; text-transform:uppercase; letter-spacing:.12em; font-size:.72rem; font-weight:700; }
    .muted { color:#64748b; }
    pre { border-radius:12px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>Codex Contributor</h1><p>Evidence before implementation. The Engineering Review travels with the pull request.</p></div>', unsafe_allow_html=True)
review_md = _read_text("engineering-review.md", "# Engineering Review\n\nNo Engineering Review artifact found yet. Run the pipeline to populate this dashboard.")
fields = _review_fields(review_md)
issue = _read_json("issue.json")
plan = _read_json("plan.json")
validation = _read_json("validation.json")
pr = _read_json("pr.json")

tab1, tab2, tab3, tab4 = st.tabs(["What you asked", "What Codex discovered", "What we changed", "The pull request"])

with tab1:
    st.markdown('<div class="eyebrow">Tab 1 · Issue intake</div>', unsafe_allow_html=True)
    title = issue.get("title") or fields.get("Issue", "Issue metadata unavailable").splitlines()[0]
    st.header(title)
    cols = st.columns(3)
    cols[0].metric("Issue", f"#{issue.get('number', '—')}")
    cols[1].metric("Repository", f"{issue.get('owner', '—')}/{issue.get('repo', '—')}")
    labels = issue.get("labels", [])
    cols[2].metric("Labels", ", ".join(labels) if labels else "none")
    st.markdown("#### Body")
    st.markdown(issue.get("body") or "Issue body is available in the GitHub link or has not been persisted yet.")

with tab2:
    st.markdown('<div class="eyebrow">Tab 2 · Investigation centerpiece</div>', unsafe_allow_html=True)
    status = _status(review_md)
    left, right = st.columns([4, 1])
    with left:
        st.markdown(f'<span class="badge">{status}</span>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="eyebrow">Confidence</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="confidence">{_confidence(review_md)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="review-card">', unsafe_allow_html=True)
    st.markdown(review_md)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="eyebrow">Tab 3 · Evidence-backed implementation</div>', unsafe_allow_html=True)
    changes = plan.get("files", [])
    if changes:
        st.subheader("Files in the plan")
        for item in changes:
            st.markdown(f"- **`{item.get('path', 'unknown')}`** — {item.get('change', '')}")
    else:
        st.info("No implementation plan artifact found yet.")
    st.subheader("Tests and validation")
    tests = plan.get("tests", [])
    st.write(", ".join(tests) if tests else "No test plan persisted yet.")
    st.json(validation if validation else {"status": "No validation summary found"})
    diff = _read_text("diff.patch")
    if diff:
        st.subheader("Diff")
        st.code(diff, language="diff")

with tab4:
    st.markdown('<div class="eyebrow">Tab 4 · Maintainer handoff</div>', unsafe_allow_html=True)
    draft = _read_text("draft-pr.md")
    if draft:
        st.markdown(draft)
    else:
        st.info("No PR draft found yet.")
    url = pr.get("url")
    if url:
        st.link_button("Open real pull request", url)
    elif pr:
        st.caption(pr.get("message", "PR content is saved locally."))
