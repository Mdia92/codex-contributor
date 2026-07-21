# Codex Contributor

**Codex Contributor makes Codex investigate before it writes: every GitHub issue gets an evidence-cited Engineering Review before a single line of code.**

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
Codex Contributor workflow: comprehend → explore → **Investigation Agent** → **Implementation Agent** → **Validation Agent** → PR
    ↓                         ↓
GPT-5.6 reasoning       Deterministic trust layer
evidence + judgment     Git, file I/O, parsers, tests, GitHub API
```

- **Investigation Agent** is the Codex reasoning stage: issue comprehension, repository exploration, cited evidence, and confidence-gate recommendation.
- **Implementation Agent** turns an approved Engineering Review into the smallest file/change/test plan and writes the scoped working-copy changes.
- **Validation Agent** runs the project test framework, reasons about failures, and caps repair attempts at five iterations.
- The **Codex Contributor workflow** coordinates the named agents, while deterministic Git, parsing, filesystem, test, and GitHub tools remain the trust layer.

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

The demo investigations were executed by Codex itself running GPT-5.6 Sol as the reasoning engine — the same workflow the API path automates — making Codex the execution layer end to end.

## Key Decisions Made During the Build

- Treat the Engineering Review as a durable artifact, not an intermediate JSON response.
- Require every evidence claim to cite a repository path and line range or symbol where available.
- Keep one confidence gate at investigation-to-implementation handoff.
- Keep deterministic tools responsible for repository facts and validation.
- Cache model responses by repository commit, issue, and prompt identity.
- Keep the dashboard read-only so presentation never causes external side effects.
- Save a local PR draft whenever credentials or publishing context are incomplete.

## Measured Results

| Measure | Result |
| --- | ---: |
| Issues analyzed | 5 |
| Evidence citations | 18 |
| Citations verified at cited path and line range | 100% (18/18) |
| Confirmed / Challenged / Human review | 5 / 0 / 0 |

See [BENCHMARK.md](BENCHMARK.md) for the full methodology and results.

## Sample repos judges can test against

| Repository | Issue | Claim under investigation | Result |
| --- | --- | --- | --- |
| [openai/openai-python](https://github.com/openai/openai-python) | [#3516](https://github.com/openai/openai-python/issues/3516) | Azure custom `api-key` across redirects | ✓ Confirmed |
| [openai/openai-python](https://github.com/openai/openai-python) | [#3459](https://github.com/openai/openai-python/issues/3459) | Null `response.output` streaming crash | ✓ Confirmed |
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | [#38989](https://github.com/langchain-ai/langchain/issues/38989) | Callback survives exceptional context exit | ✓ Confirmed |
| [pallets/flask](https://github.com/pallets/flask) | [#6093](https://github.com/pallets/flask/issues/6093) | First-colon IPv6 parsing | ✓ Confirmed |
| [psf/requests](https://github.com/psf/requests) | [#7399](https://github.com/psf/requests/issues/7399) | `verify` documentation behavior mismatch | ✓ Confirmed |

The recommended demo is `openai/openai-python#3516`. Its shareable review is copied to [examples/engineering_review_sample.md](examples/engineering_review_sample.md).

## License

Released under the [MIT License](LICENSE).
