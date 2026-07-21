from codex_contributor.cli import build_parser


def test_cli_requires_repo_and_issue():
    args = build_parser().parse_args([
        "--repo", "https://github.com/acme/demo",
        "--issue", "https://github.com/acme/demo/issues/1",
    ])
    assert args.repo.endswith("acme/demo")
    assert args.issue.endswith("issues/1")
