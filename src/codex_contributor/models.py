from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Issue:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    labels: tuple[str, ...] = ()
    url: str = ""


@dataclass(frozen=True)
class Evidence:
    path: str
    claim: str
    start_line: int | None = None
    end_line: int | None = None
    symbol: str | None = None

    @property
    def citation(self) -> str:
        anchor = self.symbol or ""
        if self.start_line is not None:
            end = self.end_line or self.start_line
            anchor = f"L{self.start_line}-L{end}"
        return f"{self.path}:{anchor}".rstrip(":")


@dataclass
class RepositoryMap:
    root: str
    files: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    test_command: list[str] | None = None
    symbols: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class EngineeringReview:
    issue: Issue
    status: Literal["issue_confirmed", "issue_challenged", "human_review_required"]
    summary: str
    evidence: list[Evidence]
    finding: str
    recommended_change: str
    confidence: float
    action: Literal["proceed", "request_human_review_before_implementation"]
    metrics: dict[str, int | float | str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)

    def validate(self, repository: RepositoryMap | None = None) -> None:
        if self.status not in {"issue_confirmed", "issue_challenged", "human_review_required"}:
            raise ValueError(f"invalid review status: {self.status}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.action == "proceed" and self.status == "human_review_required":
            raise ValueError("human_review_required cannot proceed")
        known_paths = set(repository.files) if repository else None
        for item in self.evidence:
            if not item.path or not item.claim:
                raise ValueError("every evidence item requires a path and claim")
            if known_paths is not None and item.path not in known_paths:
                raise ValueError(f"evidence cites a path outside the repository map: {item.path}")
            if item.start_line is not None and item.start_line < 1:
                raise ValueError("evidence line numbers must be positive")
            if item.end_line is not None and item.start_line is None:
                raise ValueError("end_line requires start_line")
            if item.end_line is not None and item.end_line < item.start_line:
                raise ValueError("end_line must be greater than or equal to start_line")

    @classmethod
    def from_model_dict(cls, issue: Issue, data: dict, repository: RepositoryMap) -> "EngineeringReview":
        required = {"summary", "evidence", "finding", "recommended_change", "confidence", "proceed"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"model response missing fields: {', '.join(sorted(missing))}")
        evidence = [
            Evidence(
                path=item["path"], claim=item["claim"], start_line=item.get("start_line"),
                end_line=item.get("end_line"), symbol=item.get("symbol"),
            )
            for item in data["evidence"]
        ]
        proceed = bool(data["proceed"])
        status = data.get("status") or ("issue_confirmed" if proceed else "human_review_required")
        review = cls(
            issue=issue, status=status, summary=str(data["summary"]), evidence=evidence,
            finding=str(data["finding"]), recommended_change=str(data["recommended_change"]),
            confidence=float(data["confidence"]),
            action="proceed" if proceed else "request_human_review_before_implementation",
            metrics=data.get("metrics", {}),
        )
        review.validate(repository)
        return review
