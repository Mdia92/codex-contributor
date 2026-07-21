from __future__ import annotations

import json
import os
import subprocess
import time
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

    def fork_repository(self, owner: str, repo: str) -> dict:
        """Create (or request) a fork and return its repository metadata."""
        return self._request("POST", f"/repos/{owner}/{repo}/forks", {})

    def _ref(self, owner: str, repo: str, branch: str) -> dict:
        return self._request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")

    def publish_branch(self, owner: str, repo: str, branch: str, files: dict[str, str], base: str = "main") -> str:
        """Publish complete file contents to a fork using GitHub's Git Data API."""
        if not self.token:
            raise GitHubError("GITHUB_TOKEN is required to publish a branch")
        try:
            fork = self.fork_repository(owner, repo)
        except GitHubError:
            # A fork may already exist; reuse the authenticated user's fork.
            user = self._request("GET", "/user")
            fork = self._request("GET", f"/repos/{user['login']}/{repo}")
        fork_owner = (fork.get("owner") or {}).get("login") or fork.get("owner", {}).get("name")
        fork_name = fork.get("name", repo)
        if not fork_owner:
            raise GitHubError("GitHub fork response did not include an owner")
        # Fork creation can be asynchronous for a new fork.
        base_ref = None
        for _ in range(6):
            try:
                base_ref = self._ref(fork_owner, fork_name, base)
                break
            except GitHubError:
                time.sleep(1)
        if not base_ref:
            raise GitHubError("Fork did not become available for branch publishing")
        base_sha = base_ref["object"]["sha"]
        base_commit = self._request("GET", f"/repos/{fork_owner}/{fork_name}/git/commits/{base_sha}")
        blobs = []
        for path, content in files.items():
            blob = self._request("POST", f"/repos/{fork_owner}/{fork_name}/git/blobs", {"content": content, "encoding": "utf-8"})
            blobs.append({"path": path.replace("\\", "/"), "mode": "100644", "type": "blob", "sha": blob["sha"]})
        tree = self._request("POST", f"/repos/{fork_owner}/{fork_name}/git/trees", {"base_tree": base_commit["tree"]["sha"], "tree": blobs})
        commit = self._request("POST", f"/repos/{fork_owner}/{fork_name}/git/commits", {"message": "feat: apply evidence-backed contribution", "tree": tree["sha"], "parents": [base_sha]})
        try:
            self._request("POST", f"/repos/{fork_owner}/{fork_name}/git/refs", {"ref": f"refs/heads/{branch}", "sha": commit["sha"]})
        except GitHubError:
            self._request("PATCH", f"/repos/{fork_owner}/{fork_name}/git/refs/heads/{branch}", {"sha": commit["sha"], "force": True})
        return f"{fork_owner}:{branch}"
