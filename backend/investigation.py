"""Public backend entry point; implementation lives in the installable package."""

from codex_contributor.backend.investigation import InvestigationResult, investigate

__all__ = ["InvestigationResult", "investigate"]

