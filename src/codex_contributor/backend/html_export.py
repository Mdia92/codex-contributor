from __future__ import annotations

import html
import re
from pathlib import Path


TEMPLATE = Path(__file__).with_name("templates") / "engineering_review.html"


def _sections(markdown: str) -> tuple[str, list[tuple[str, str]]]:
    title = "Engineering Review"
    match = re.search(r"^# (.+)$", markdown, re.MULTILINE)
    if match:
        title = match.group(1).strip()
    headings = list(re.finditer(r"^## (.+)$", markdown, re.MULTILINE))
    sections = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        body = markdown[heading.end():end].strip()
        sections.append((heading.group(1).strip(), body))
    return title, sections


def _body_html(body: str) -> str:
    escaped = html.escape(body)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    lines = escaped.splitlines()
    rendered = []
    in_list = False
    for line in lines:
        if line.startswith("- "):
            if not in_list:
                rendered.append("<ul>")
                in_list = True
            rendered.append(f"<li>{line[2:]}</li>")
        else:
            if in_list:
                rendered.append("</ul>")
                in_list = False
            if line.strip():
                rendered.append(f"<p>{line}</p>")
    if in_list:
        rendered.append("</ul>")
    return "\n".join(rendered)


def render_review_html(markdown: str) -> str:
    title, sections = _sections(markdown)
    cards = []
    for name, body in sections:
        css = "section-card confidence-card" if name.lower() == "confidence" else "section-card"
        cards.append(f'<section class="{css}"><div class="section-kicker">{html.escape(name)}</div><div class="section-body">{_body_html(body)}</div></section>')
    template = TEMPLATE.read_text(encoding="utf-8")
    return template.replace("{{TITLE}}", html.escape(title)).replace("{{SECTIONS}}", "\n".join(cards))


def export_review(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_review_html(input_path.read_text(encoding="utf-8")), encoding="utf-8")
    return output_path

