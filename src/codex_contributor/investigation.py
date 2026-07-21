from __future__ import annotations

from .models import EngineeringReview, Issue, RepositoryMap


def build_stub_review(issue: Issue, repository: RepositoryMap) -> EngineeringReview:
    """Produce the batch-one artifact without pretending model investigation occurred."""
    return EngineeringReview(
        issue=issue,
        status="human_review_required",
        summary="Repository intake completed; evidence-based model investigation has not run yet.",
        evidence=[],
        finding="The deterministic trust layer mapped the repository, but there is not yet enough cited evidence to assess the issue.",
        recommended_change="Run the GPT-5.6 investigation stage before modifying code.",
        confidence=0.0,
        action="request_human_review_before_implementation",
        metrics={
            "files_explored": len(repository.files),
            "symbols_indexed": sum(len(items) for items in repository.symbols.values()),
            "evidence_citations": 0,
            "languages_detected": len(repository.languages),
        },
    )

