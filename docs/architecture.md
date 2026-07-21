# Architecture

```text
GitHub Issue URL / repository URL
                │
                ▼
      ┌─────────────────────┐
      │ Issue comprehension │  GitHub API: issue, labels, body
      └──────────┬──────────┘
                 ▼
      ┌─────────────────────┐
      │ Repository explorer │  clone, file tree, symbols, test runner
      └──────────┬──────────┘
                 ▼
      ┌─────────────────────┐
      │ Investigation Agent │  GPT-5.6 + cited evidence + confidence gate
      └──────────┬──────────┘
                 ▼
       confidence < 0.50? ── yes ──► Engineering Review + human review
                 │ no
                 ▼
      ┌─────────────────────┐
      │ Implementation Agent│  files, changes, tests
      └──────────┬──────────┘
                 ▼
      ┌─────────────────────┐
      │ Implementation Agent│  one cached model call per file
      └──────────┬──────────┘
                 ▼
      ┌─────────────────────┐
      │ Validation Agent    │  tests → failure repair, max 5 iterations
      └──────────┬──────────┘
                 ▼
      ┌─────────────────────┐
      │ PR generator        │  review → plan → validation → PR body
      └──────────┬──────────┘
                 ▼
      fork + branch + commit + pull request, or local draft-pr.md
```

## Stage responsibilities

1. **Issue comprehension** uses the GitHub API to create a typed issue contract.
2. **Repository exploration** uses deterministic Git, filesystem, AST, and test-runner tooling. It does not ask a model to invent repository facts.
3. The **Investigation Agent** sends the issue and line-numbered repository excerpts to GPT-5.6 Sol. The prompt requires file-level evidence for every codebase claim. Its structured review is cached and validated.
4. **Confidence gate** stops implementation below 0.50 and emits a Human Review Required section.
5. The **Implementation Agent** converts the review into a minimal file/change/test plan.
6. The **Implementation Agent** makes one complete-file model call per planned file, caches it, and rejects paths outside the working copy.
7. The **Validation Agent** runs the detected framework. Only failures invoke repair calls, and the loop stops after five iterations.
8. **PR generation** embeds the Engineering Review first, then the plan and validation summary. It publishes through the GitHub Git Data API when configured, otherwise saves a draft.

The Streamlit dashboard consumes persisted artifacts and has no authority to invoke models or write to GitHub.
