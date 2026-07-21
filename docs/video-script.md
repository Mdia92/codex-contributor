# Three-minute demo script

## 0:00–0:15 — Hook

Show a GitHub issues page crowded with open work.

“Every AI coding tool takes a task and executes. Codex Contributor asks a more important question first: is this actually the right change? It investigates the repository, weighs evidence, and produces an Engineering Review before writing code.”

## 0:15–0:25 — Workflow comparison

Show the two diagrams: junior `Issue → Code`; careful engineer `Issue → Question → Read → Understand → Investigate → Implement → Verify → PR`.

“A junior contributor goes from issue to code. A careful engineer investigates first. Codex Contributor automates the second workflow.”

## 0:25–1:30 — Investigation hero

Run `codex-contributor run --repo <url> --issue <number>` and show Tab 1.

“Point it at a real issue. Codex reads the issue, maps the repository, and gathers line-level evidence.”

Switch to Tab 2 as the Engineering Review appears. Hold the completed Review on screen for five seconds.

“This is the product: a document a maintainer can verify. It says what was investigated, what the evidence shows, what finding follows, and how confident the recommendation is. Every claim is tied to a file, line range, or symbol.”

## 1:30–2:15 — Implementation and validation

Show Tab 3: planned files, changes, tests, and validation iterations.

“Only after the confidence gate passes does Codex plan and write changes. It runs the project’s own tests. If a test fails, the repair loop reads the failure, patches the working copy, and tries again—up to five iterations.”

## 2:15–2:45 — Pull request

Show Tab 4 and the generated PR body.

“The Engineering Review is the first section of the pull request. The implementation plan and validation summary follow it, so the maintainer receives the reasoning and the diff together.”

## 2:45–3:00 — Close

Hold on the Engineering Review again.

“Codex Contributor does not replace maintainers. It makes AI-authored contributions easier to investigate, verify, and trust. Codex built Codex Contributor.”

