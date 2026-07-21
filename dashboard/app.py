from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".codex-contributor"
OUTPUT_DIR = Path(st.sidebar.text_input("Artifact directory", str(DEFAULT_OUTPUT))).expanduser()


def _candidate_dirs() -> list[Path]:
    return [OUTPUT_DIR, DEFAULT_OUTPUT / "work" / ".codex-contributor", DEFAULT_OUTPUT / "work"]


def _find(name: str) -> Path | None:
    for directory in _candidate_dirs():
        path = directory / name
        if path.exists():
            return path
    return None


def _text(name: str) -> str:
    path = _find(name)
    return path.read_text(encoding="utf-8", errors="replace") if path else ""


def _json(name: str) -> dict[str, Any]:
    path = _find(name)
    if not path:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _sections(markdown: str) -> list[tuple[str, str]]:
    headings = list(re.finditer(r"^## (.+)$", markdown, re.MULTILINE))
    return [(match.group(1).strip(), markdown[match.end():(headings[index + 1].start() if index + 1 < len(headings) else len(markdown))].strip()) for index, match in enumerate(headings)]


def _inline(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def _body(value: str) -> str:
    lines = []
    list_open = False
    for line in value.splitlines():
        if line.startswith("- "):
            if not list_open:
                lines.append("<ul>")
                list_open = True
            lines.append(f"<li>{_inline(line[2:])}</li>")
        else:
            if list_open:
                lines.append("</ul>")
                list_open = False
            if line.strip():
                lines.append(f"<p>{_inline(line)}</p>")
    if list_open:
        lines.append("</ul>")
    return "".join(lines) or '<p class="empty-copy">Evidence is not available yet. The document will populate after intake.</p>'


def _status(markdown: str) -> tuple[str, str]:
    if "Issue Challenged" in markdown:
        return "⚠ Issue Challenged", "challenged"
    if "Human Review Required" in markdown or "human_review_required" in markdown:
        return "Human Review Required", "human"
    if "Issue Confirmed" in markdown:
        return "✓ Issue Confirmed", "confirmed"
    return "Investigation pending", "pending"


def _confidence(markdown: str) -> int | None:
    match = re.search(r"## Confidence\s+([0-9]+)%", markdown)
    return int(match.group(1)) if match else None


st.set_page_config(page_title="Codex Contributor", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root { --ink:#142033; --muted:#64748b; --line:#dce4ef; --paper:#fff; --wash:#f3f6fb; --blue:#2d5db2; }
.stApp { background:var(--wash); color:var(--ink); }
[data-testid="stSidebar"] { background:#101a2b; }
[data-testid="stSidebar"] * { color:#dce7fa !important; }
.hero { background:linear-gradient(125deg,#0e1829,#254a88); color:white; border-radius:22px; padding:2.5rem 2.8rem; box-shadow:0 18px 45px rgba(19,39,74,.18); margin:0 0 1.4rem; }
.hero .kicker, .eyebrow { color:#8eb3f5; text-transform:uppercase; letter-spacing:.16em; font:800 .68rem 'DM Sans',sans-serif; }
.hero h1 { font:500 2.45rem 'Libre Baskerville',Georgia,serif; margin:.65rem 0 .45rem; letter-spacing:-.04em; }
.hero p { color:#c6d7f4; font:400 1rem 'DM Sans',sans-serif; margin:0; }
.meta-strip { display:flex; gap:1.4rem; margin-top:1.5rem; color:#b4c9ec; font:.82rem 'DM Sans',sans-serif; }
.meta-strip strong { color:#fff; }
.review-shell { background:var(--paper); border:1px solid var(--line); border-radius:19px; padding:1.25rem 1.35rem 1.4rem; box-shadow:0 12px 30px rgba(36,56,91,.08); }
.review-header { display:flex; justify-content:space-between; align-items:flex-start; gap:2rem; border-bottom:1px solid var(--line); padding:.4rem .35rem 1.2rem; margin-bottom:.9rem; }
.review-title { font:700 1.5rem 'Libre Baskerville',Georgia,serif; color:var(--ink); margin:.45rem 0 0; }
.badge { display:inline-flex; align-items:center; border-radius:999px; padding:.42rem .76rem; font:700 .74rem 'DM Sans',sans-serif; }
.badge.confirmed { background:#e3f7ec; color:#167044; } .badge.challenged { background:#fff0d9; color:#9a5b00; } .badge.human { background:#f1e8ff; color:#7041a5; } .badge.pending { background:#edf2f8; color:#526173; }
.score { min-width:112px; text-align:right; } .score-label { color:var(--muted); text-transform:uppercase; letter-spacing:.13em; font:800 .63rem 'DM Sans',sans-serif; } .score-value { color:var(--blue); font:800 2.8rem 'DM Sans',sans-serif; line-height:1.05; }
.doc-section { border:1px solid var(--line); border-radius:13px; margin:.72rem 0; padding:1rem 1.2rem; background:#fff; }
.doc-section.confidence-section { border-color:#a9c4ef; background:#fafdff; } .doc-section.human-section { border-color:#d8bff2; background:#fcf9ff; }
.doc-label { color:var(--blue); text-transform:uppercase; letter-spacing:.13em; font:800 .66rem 'DM Sans',sans-serif; margin-bottom:.45rem; } .doc-body { color:#25334a; font:400 1rem/1.75 'Libre Baskerville',Georgia,serif; } .doc-body p { margin:.15rem 0 .5rem; } .doc-body ul { margin:.2rem 0 .3rem 1.2rem; padding:0; } .doc-body li { margin:.35rem 0; }
code { color:#25509c; background:#edf3ff; border-radius:5px; padding:.12rem .35rem; font:500 .83em ui-monospace,Consolas,monospace; } .empty-copy { color:var(--muted); font-style:italic; }
.metric-card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; min-height:108px; } .metric-label { color:var(--muted); font:700 .68rem 'DM Sans',sans-serif; letter-spacing:.1em; text-transform:uppercase; } .metric-value { color:var(--ink); font:700 1.1rem 'DM Sans',sans-serif; margin-top:.5rem; word-break:break-word; }
.empty-panel { text-align:center; background:#fff; border:1px dashed #b8c7dc; border-radius:16px; padding:3rem 2rem; color:var(--muted); } .empty-panel h3 { color:var(--ink); font:700 1.25rem 'Libre Baskerville',Georgia,serif; }
.trace-table { width:100%; border-collapse:separate; border-spacing:0 .5rem; margin-top:.45rem; } .trace-table th { color:var(--muted); text-align:left; text-transform:uppercase; letter-spacing:.1em; font:800 .65rem 'DM Sans',sans-serif; padding:.2rem .75rem; } .trace-table td { background:#fff; border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:.75rem; color:#25334a; font:.87rem 'DM Sans',sans-serif; } .trace-table td:first-child { border-left:1px solid var(--line); border-radius:10px 0 0 10px; font-weight:800; } .trace-table td:last-child { border-right:1px solid var(--line); border-radius:0 10px 10px 0; }
.stTabs [data-baseweb="tab-list"] { gap:.35rem; } .stTabs [data-baseweb="tab"] { font:700 .86rem 'DM Sans',sans-serif; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="kicker">Codex Contributor workflow</div><h1>Codex Contributor</h1><p>Codex Contributor makes Codex investigate before it writes: every GitHub issue gets an evidence-cited Engineering Review before a single line of code.</p><div class="meta-strip"><span><strong>4</strong> narrative tabs</span><span><strong>3</strong> named agents</span><span><strong>0</strong> dashboard model calls</span></div></div>', unsafe_allow_html=True)

review_md = _text("engineering-review.md")
issue = _json("issue.json")
plan = _json("plan.json")
validation = _json("validation.json")
pr = _json("pr.json")
trace = _json("execution-trace.json").get("stages", [])
status, status_class = _status(review_md)
confidence = _confidence(review_md)
sections = _sections(review_md)

tab1, tab2, tab3, tab4 = st.tabs(["What you asked", "What Codex discovered", "What we changed", "The pull request"])

with tab1:
    st.markdown('<div class="eyebrow">Tab 1 · Issue intake</div>', unsafe_allow_html=True)
    if issue:
        st.markdown(f"## {html.escape(str(issue.get('title', 'Untitled issue')))}")
        cols = st.columns(3)
        for col, label, value in zip(cols, ["Issue", "Repository", "Labels"], [f"#{issue.get('number', '—')}", f"{issue.get('owner', '—')}/{issue.get('repo', '—')}", ", ".join(issue.get('labels', [])) or "none"]):
            col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{html.escape(str(value))}</div></div>', unsafe_allow_html=True)
        st.markdown("### Issue body")
        st.markdown(issue.get("body") or "This issue has no body.")
    else:
        st.markdown('<div class="empty-panel"><h3>Issue intake is ready</h3><p>Run the pipeline to bring the GitHub issue into the first story beat.</p></div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="eyebrow">Tab 2 · Investigation Agent</div>', unsafe_allow_html=True)
    if review_md:
        badge = f'<span class="badge {status_class}">{html.escape(status)}</span>'
        score = f"{confidence}%" if confidence is not None else "—"
        cards = []
        for name, body in sections:
            lower = name.lower()
            extra = " confidence-section" if lower == "confidence" else " human-section" if "human review" in lower else ""
            cards.append(f'<section class="doc-section{extra}"><div class="doc-label">{html.escape(name)}</div><div class="doc-body">{_body(body)}</div></section>')
        st.markdown(f'<article class="review-shell"><div class="review-header"><div>{badge}<div class="review-title">Engineering Review</div></div><div class="score"><div class="score-label">Confidence</div><div class="score-value">{score}</div></div></div>{"".join(cards)}</article>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-panel"><h3>Your review will live here</h3><p>This is the flagship artifact. Once intake completes, each evidence-backed section will appear as a composed engineering document.</p></div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="eyebrow">Tab 3 · Implementation Agent + Validation Agent</div>', unsafe_allow_html=True)
    if plan:
        st.subheader("Implementation plan")
        st.markdown(plan.get("rationale", ""))
        for item in plan.get("files", []):
            st.markdown(f"- **`{item.get('path', 'unknown')}`** — {item.get('change', '')}")
        st.subheader("Tests and validation")
        st.write(", ".join(plan.get("tests", [])) or "No test plan specified.")
        st.json(validation or {"status": "Validation has not run yet."})
        diff = _text("diff.patch")
        if diff:
            st.subheader("Diff")
            st.code(diff, language="diff")
    else:
        st.markdown('<div class="empty-panel"><h3>Implementation evidence is staged</h3><p>The plan, file changes, and validation loop will appear here after the confidence gate permits implementation.</p></div>', unsafe_allow_html=True)
    st.subheader("Execution trace")
    if isinstance(trace, list) and trace:
        rows = "".join(
            f"<tr><td>{html.escape(str(item.get('stage', 'Unknown stage')))}</td><td>{html.escape(str(item.get('duration_ms', '—')))} ms</td><td>{html.escape(str(item.get('decision', '—')))}</td></tr>"
            for item in trace if isinstance(item, dict)
        )
        st.markdown(f'<table class="trace-table"><thead><tr><th>Stage</th><th>Duration</th><th>Decision</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-panel"><h3>Execution trace will appear here</h3><p>Each run records the Investigation, Implementation, Validation, and pull-request handoff decisions without invoking the dashboard itself.</p></div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="eyebrow">Tab 4 · Maintainer handoff</div>', unsafe_allow_html=True)
    draft = _text("draft-pr.md")
    if draft:
        st.markdown('<div class="review-shell">' + _body(draft) + '</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-panel"><h3>The pull request is waiting</h3><p>A locally saved draft or real PR link will appear here after validation.</p></div>', unsafe_allow_html=True)
    if pr.get("url"):
        st.link_button("Open real pull request", pr["url"])
    elif pr.get("message"):
        st.caption(pr["message"])
