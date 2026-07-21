from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from .engineering_review import render_markdown
from .github_client import GitHubClient
from .investigation import build_stub_review
from .issue_parser import parse_issue_url, parse_repo_url
from .models import EngineeringReview, RepositoryMap
from .repo_explorer import map_repository


@dataclass
class IntakeResult:
    review: EngineeringReview
    repository: RepositoryMap
    markdown: str
    clone_path: Path


def run_intake(repo_url: str, issue_url: str, workspace: Path | None = None, client: GitHubClient | None = None) -> IntakeResult:
    repo_owner, repo_name = parse_repo_url(repo_url)
    issue_owner, issue_repo, issue_number = parse_issue_url(issue_url)
    if (repo_owner.lower(), repo_name.lower()) != (issue_owner.lower(), issue_repo.lower()):
        raise ValueError("Repository URL and issue URL must refer to the same GitHub repository")
    client = client or GitHubClient()
    issue = client.get_issue(issue_owner, issue_repo, issue_number)
    base = workspace or Path(tempfile.mkdtemp(prefix="codex-contributor-"))
    clone_path = base / repo_name
    client.clone(repo_url, clone_path)
    repository = map_repository(clone_path)
    review = build_stub_review(issue, repository)
    return IntakeResult(review, repository, render_markdown(review), clone_path)

