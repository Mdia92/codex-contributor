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

