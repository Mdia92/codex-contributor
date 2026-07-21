from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from .models import Issue


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str | None = None, api_url: str = "https://api.github.com") -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.api_url = api_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "codex-contributor/0.1"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(f"{self.api_url}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise GitHubError(f"GitHub API returned {exc.code}: {detail}") from exc

    def get_issue(self, owner: str, repo: str, number: int) -> Issue:
        data = self._request("GET", f"/repos/{owner}/{repo}/issues/{number}")
        if "pull_request" in data:
            raise GitHubError(f"#{number} is a pull request, not an issue")
        return Issue(
            owner=owner,
            repo=repo,
            number=number,
            title=data["title"],
            body=data.get("body") or "",
            labels=tuple(label["name"] for label in data.get("labels", [])),
            url=data.get("html_url", ""),
        )

    def clone(self, repo_url: str, destination: Path, depth: int = 1) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--depth", str(depth), repo_url, str(destination)],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise GitHubError(result.stderr.strip() or "git clone failed")
        return destination

    def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: str) -> str:
        if not self.token:
            raise GitHubError("GITHUB_TOKEN is required to open a pull request")
        result = self._request("POST", f"/repos/{owner}/{repo}/pulls", {
            "title": title, "head": head, "base": base, "body": body
        })
        return result["html_url"]

