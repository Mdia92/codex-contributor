import pytest

from codex_contributor.issue_parser import parse_issue_url, parse_repo_url


def test_parse_issue_url():
    assert parse_issue_url("https://github.com/openai/openai-python/issues/123") == ("openai", "openai-python", 123)


def test_parse_repo_url_accepts_git_suffix():
    assert parse_repo_url("https://github.com/openai/openai-python.git") == ("openai", "openai-python")


def test_parse_issue_url_rejects_non_issue():
    with pytest.raises(ValueError):
        parse_issue_url("https://github.com/openai/openai-python")

