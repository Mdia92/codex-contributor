from __future__ import annotations

from .models import EngineeringReview


STATUS = {
    "issue_confirmed": "✓ Issue Confirmed",
    "issue_challenged": "⚠ Issue Challenged",
    "human_review_required": "◊ Human Review Required",
}


def render_markdown(review: EngineeringReview) -> str:
    evidence = "\n".join(f"- `{item.citation}` — {item.claim}" for item in review.evidence) or "- No codebase claims yet; live investigation is pending."
    metrics = "\n".join(f"- **{key.replace('_', ' ').title()}:** {value}" for key, value in review.metrics.items())
    return f"""# Engineering Review

> {STATUS[review.status]} · **Confidence {review.confidence:.0%}**

## Issue

[{review.issue.owner}/{review.issue.repo}#{review.issue.number}: {review.issue.title}]({review.issue.url})

## Summary

{review.summary}

## Evidence

{evidence}

## Finding

{review.finding}

## Recommended Change

{review.recommended_change}

## Decision

`{review.action}`

## Investigation Metrics

{metrics or '- Metrics unavailable'}
"""

