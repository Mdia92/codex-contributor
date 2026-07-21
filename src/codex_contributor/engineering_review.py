from __future__ import annotations

from .models import EngineeringReview


STATUS = {
    "issue_confirmed": "✓ Issue Confirmed",
    "issue_challenged": "⚠ Issue Challenged",
    "human_review_required": "◊ Human Review Required",
}


def render_markdown(review: EngineeringReview) -> str:
    evidence = "\n".join(f"- `{item.citation}` — {item.claim}" for item in review.evidence) or "- No codebase claims yet; live investigation is pending."
    return f"""# Engineering Review

## Issue

[{review.issue.owner}/{review.issue.repo}#{review.issue.number}: {review.issue.title}]({review.issue.url})

**Status:** {STATUS[review.status]}

## Summary

{review.summary}

## Evidence

{evidence}

## Finding

{review.finding}

## Recommended Change

{review.recommended_change}

## Confidence

{review.confidence:.0%}

## Proceed

{"Yes" if review.action == "proceed" else "No — maintainer review required before implementation."}
"""
