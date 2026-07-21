# Three-minute demo script

## 0:00-0:15 — Hook

Show a GitHub issues page crowded with open work.

“Every AI coding tool takes a task and executes. Codex Contributor asks a more important question first: is this actually the right change? It investigates the repository, weighs evidence, and produces an Engineering Review before writing code.”

## 0:15-0:25 — Workflow comparison

Show the two diagrams: junior `Issue → Code`; careful engineer `Issue → Question → Read → Understand → Investigate → Implement → Verify → PR`.

“A junior contributor goes from issue to code. A careful engineer investigates first. The Codex Contributor workflow coordinates Investigation, Implementation, and Validation Agents to automate the second workflow.”

## 0:25-1:30 — Investigation hero

Show the selected demo: `openai/openai-python` issue #3516. Open Tab 1, then switch to Tab 2 as the Engineering Review appears. Hold the completed Review on screen for five seconds.

“This issue claims that cross-origin redirects strip `Authorization` but can retain Azure’s custom `api-key`. The Investigation Agent reads the issue, maps the repository, and gathers line-level evidence.”

“Here is the finding: the default client enables redirects in `src/openai/_base_client.py:L835-L839`, while Azure injects `api-key` in `src/openai/lib/azure.py:L382-L386`. The Engineering Review confirms the claim at 0.94 confidence. Every evidence bullet is tied to a file and line range; the confidence gate blocks implementation below 0.50.”

## 1:30-2:15 — Implementation and validation

Show Tab 3: planned files, changes, tests, validation iterations, and the execution trace.

“Only after the confidence gate passes does the Implementation Agent plan and write changes. The Validation Agent runs the project’s own tests. If a test fails, the repair loop reads the failure, patches the working copy, and tries again—up to five iterations.”

## 2:15-2:45 — Pull request

Show Tab 4 and the generated PR body.

“The Engineering Review is the first section of the pull request. The implementation plan and validation summary follow it, so the maintainer receives the reasoning and the diff together.”

## 2:45-3:00 — Close

Hold on the Engineering Review again.

“Codex Contributor does not replace maintainers. It makes AI-authored contributions easier to investigate, verify, and trust. Codex built Codex Contributor.”
