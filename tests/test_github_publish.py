from codex_contributor.github_client import GitHubClient


def test_publish_branch_uses_mocked_git_data_api_only():
    class MockClient(GitHubClient):
        def __init__(self):
            super().__init__(token="mock")
            self.calls = []
            self.blob_number = 0

        def _request(self, method, path, payload=None):
            self.calls.append((method, path, payload))
            if method == "POST" and path.endswith("/forks"):
                return {"name": "demo", "owner": {"login": "Mdia92"}}
            if method == "GET" and "/git/ref/heads/" in path:
                return {"object": {"sha": "base-sha"}}
            if method == "GET" and "/git/commits/" in path:
                return {"tree": {"sha": "base-tree"}}
            if method == "POST" and path.endswith("/git/blobs"):
                self.blob_number += 1
                return {"sha": f"blob-{self.blob_number}"}
            if method == "POST" and path.endswith("/git/trees"):
                return {"sha": "tree-sha"}
            if method == "POST" and path.endswith("/git/commits"):
                return {"sha": "commit-sha"}
            if method == "POST" and path.endswith("/git/refs"):
                return {"ref": "refs/heads/codex"}
            raise AssertionError(f"unexpected mocked request: {method} {path}")

    client = MockClient()
    head = client.publish_branch("acme", "demo", "codex", {"src/app.py": "print('ok')"})
    assert head == "Mdia92:codex"
    assert [call[0:2] for call in client.calls] == [
        ("POST", "/repos/acme/demo/forks"),
        ("GET", "/repos/Mdia92/demo/git/ref/heads/main"),
        ("GET", "/repos/Mdia92/demo/git/commits/base-sha"),
        ("POST", "/repos/Mdia92/demo/git/blobs"),
        ("POST", "/repos/Mdia92/demo/git/trees"),
        ("POST", "/repos/Mdia92/demo/git/commits"),
        ("POST", "/repos/Mdia92/demo/git/refs"),
    ]

