# Codex Contributor

Codex Contributor turns GitHub issues into evidence-based pull requests by investigating the repository first, verifying the issue against the actual codebase, and only then implementing and validating the recommended solution.

Every pull request includes a structured Engineering Review that explains the evidence, the findings, the recommendation, and the confidence behind the proposed change.

The tool treats an issue as a hypothesis rather than an unquestionable specification. It reads the issue, maps the repository with deterministic tools, asks GPT-5.6 to weigh cited evidence, applies a confidence gate, plans the smallest change, writes code, validates it, and prepares a pull request whose first section is the Engineering Review.

The result is an evidence-based contribution for maintainers: not just a diff, but a durable explanation of what was investigated and why the recommended change takes this form.

Codex is the autonomous engineering workflow. GPT-5.6 is the reasoning engine. Deterministic Git, filesystem, parsing, test, and GitHub tools form the trust layer.

