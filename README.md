# Codex Contributor

**Codex Contributor turns GitHub issues into evidence-based pull requests by investigating the repository first, verifying the issue against the actual codebase, and only then implementing and validating the recommended solution.**

Every pull request includes a structured Engineering Review that explains the evidence, the findings, the recommendation, and the confidence behind the proposed change.

Every analyzed issue produces an Engineering Review before any code is written.

![Engineering Review hero screenshot](docs/hero-screenshot.png)

## Philosophy

The goal isn't to replace maintainers. It's to ensure every AI-generated pull request arrives with the same investigation and justification you'd expect from an experienced contributor.

The Engineering Review is the artifact that travels with the pull request. When evidence is weak, the confidence gate requests human review before implementation.

## The careful-engineer workflow

A junior contributor often follows:

```text
Issue → Code
```

A careful engineer follows:

```text
Issue → Question → Read → Understand → Investigate → Implement → Verify → PR
```

Codex Contributor automates the second workflow and keeps the reasoning visible.

## Architecture

```text
GitHub Issue
    ↓
Codex workflow: comprehend → explore → investigate → plan → implement → validate → PR
    ↓                         ↓
GPT-5.6 reasoning       Deterministic trust layer
evidence + judgment     Git, file I/O, parsers, tests, GitHub API
```

- **Codex** is the engineering workflow: stages, tool calls, orchestration, and repair loop.
- **GPT-5.6** is the reasoning engine: issue comprehension, evidence weighing, recommendation, and plan generation.
- **Deterministic tools** are the trust layer: repository mapping, Git operations, test runners, file I/O, and GitHub API calls.

See [docs/architecture.md](docs/architecture.md) for the complete stage description.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,ai,dashboard]"
.venv\Scripts\python -m pytest
```

Copy `.env.example` to `.env` and fill credentials locally. `.env` is ignored by Git and is never required for mocked tests.

## Usage

Create an Engineering Review and run the full pipeline:

```powershell
codex-contributor run --repo https://github.com/OWNER/REPO --issue 123
```

Export any Markdown Engineering Review as a shareable HTML document:

```powershell
codex-contributor export-review --input .codex-contributor/work/engineering-review.md --output .codex-contributor/work/engineering-review.html
```

Launch the read-only dashboard:

```powershell
.venv\Scripts\streamlit run dashboard\app.py
```

The dashboard reads pipeline artifacts only and never triggers model calls.

## How Codex Was Used

Codex was used as the primary engineering workflow for the project: it inspected the proposal, created the repository foundation, implemented deterministic intake, added the GPT-5.6 investigation contract with mocked tests, built the planner/writer/validation/PR stages, and then polished the dashboard and submission artifacts. The central build decision remained stable throughout: evidence must precede edits, and unsupported claims must not enter the Engineering Review.

## Key Decisions Made During the Build

- Treat the Engineering Review as a durable artifact, not an intermediate JSON response.
- Require every evidence claim to cite a repository path and line range or symbol where available.
- Keep one confidence gate at investigation-to-implementation handoff.
- Keep deterministic tools responsible for repository facts and validation.
- Cache model responses by repository commit, issue, and prompt identity.
- Keep the dashboard read-only so presentation never causes external side effects.
- Save a local PR draft whenever credentials or publishing context are incomplete.

## Sample repos judges can test against

Batch 5 will add selected real repositories, issue URLs, and representative Engineering Review artifacts here. Until then, use any public GitHub repository with an open issue and run the mocked test suite locally.

## License

Released under the [MIT License](LICENSE).
