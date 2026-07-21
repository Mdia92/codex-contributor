# Codex Contributor

Codex Contributor turns GitHub issues into evidence-based pull requests by investigating the repository first, verifying the issue against the actual codebase, and only then implementing and validating the recommended solution.

Every analyzed issue produces a structured Engineering Review before any code is written. The artifact explains the evidence, finding, recommendation, confidence, and whether implementation should proceed.

## Build status

The deterministic foundation and mocked live-investigation integration are runnable today:

- GitHub issue intake and shallow repository cloning
- Repository file, language, Python symbol, and test-runner discovery
- Typed issue, evidence, repository-map, and Engineering Review contracts
- CLI orchestration that emits an honest stub Engineering Review
- Policy-as-code limits and an isolated PR-opening method
- Automated tests that require the pre-code artifact
- Responses API adapter using `gpt-5.6-sol` with explicit medium reasoning
- Strict structured-output validation and repository-path citation enforcement
- Commit/issue/prompt-addressed response cache under `.codex-contributor/cache/`
- Per-call token usage and estimated-cost reporting
- A no-key state that guarantees no live API request is attempted
- Structured planner, per-file writer, five-iteration validation loop, and PR draft generator
- Single `run` command that chains investigation through validation and PR preparation

The live adapter is covered only by mocked responses so far. No paid OpenAI request has been made. Implementation, repair, and dashboard stages remain future batches.

## Full pipeline command

```powershell
codex-contributor run --repo https://github.com/OWNER/REPO --issue 123
```

The pipeline clones into `.codex-contributor/work`, writes the Engineering Review, applies the confidence gate, plans and writes changes, runs the detected test framework for at most five iterations, and saves `.codex-contributor/draft-pr.md` when a PR cannot be opened. A missing API key stops safely after the review stage.

## Dashboard

Install the optional dashboard dependency and launch the read-only four-tab narrative view:

```powershell
.venv\Scripts\python -m pip install -e ".[dashboard]"
.venv\Scripts\streamlit run dashboard\app.py
```

The dashboard reads `.codex-contributor` artifacts only; it never triggers model calls. Use the sidebar to point it at another output directory.

The ignored workspace `.env` file is loaded automatically at runtime. Fill `OPENAI_API_KEY` and `GITHUB_TOKEN` there, save it, and keep it out of Git.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

Public issue intake works without authentication at GitHub's lower anonymous rate limit. Set `GITHUB_TOKEN` for authenticated API calls and future PR creation. Set `OPENAI_API_KEY` only when you are ready to permit a paid live investigation.

Install the optional live-model and YAML policy dependencies with `pip install -e ".[ai,policy]"` when those stages are enabled. A missing `OPENAI_API_KEY` produces a clear disabled state without attempting a request.

## Usage

```powershell
codex-contributor --repo https://github.com/OWNER/REPO --issue https://github.com/OWNER/REPO/issues/123 --output engineering-review.md
```

## Engineering workflow

```text
Issue → Question assumptions → Read architecture → Gather cited evidence
      → Engineering Review → Implement → Verify → PR with reasoning
```

Codex is the autonomous engineering workflow. GPT-5.6 is the reasoning engine for evidence weighing and recommendation writing. Deterministic tools—Git, parsers, test runners, file I/O, and the GitHub API—form the trust layer.

## Philosophy

The goal isn't to replace maintainers. It's to ensure every AI-generated pull request arrives with the same investigation and justification you'd expect from an experienced contributor.

The Engineering Review is the durable artifact that travels with the pull request. If the evidence is weak, the system requests maintainer review and skips implementation.

## How Codex was used

The project was initialized and its deterministic foundation implemented in the primary OpenAI Build Week Codex task on July 21, 2026. The build preserves the proposal's central decision: evidence must precede edits, and unsupported claims must never appear in the Engineering Review.

## Key decisions made during the build

- Keep the CLI usable without secrets and never fake model investigation.
- Use `gpt-5.6-sol` through the Responses API for the future quality-first investigation adapter.
- Make evidence a typed first-class object with path plus line range or symbol.
- Keep the single confidence gate in `config/policy.yaml`.
- Separate external PR writes from the safe, local intake pipeline.
