from __future__ import annotations

import re


_ISSUE_URL = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<number>\d+)/?$"
)


def parse_issue_url(url: str) -> tuple[str, str, int]:
    match = _ISSUE_URL.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub issue URL like https://github.com/owner/repo/issues/123")
    return match["owner"], match["repo"], int(match["number"])


def parse_repo_url(url: str) -> tuple[str, str]:
    cleaned = url.strip().removesuffix(".git").rstrip("/")
    match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)$", cleaned)
    if not match:
        raise ValueError("Only HTTPS GitHub repository URLs are supported in batch one")
    return match.group(1), match.group(2)

