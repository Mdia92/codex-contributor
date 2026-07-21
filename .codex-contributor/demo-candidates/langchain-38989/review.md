# Engineering Review

## Issue

langchain-ai/langchain#38989 — `get_usage_metadata_callback` keeps tracking after its `with` block raises.

## Summary

The callback context manager installs a `ContextVar`, yields control, and clears the variable only on normal generator resumption. An exception raised inside the `with` body skips the final reset statement.

## Evidence

- `libs/core/langchain_core/callbacks/usage.py:L80-L83` — `get_usage_metadata_callback` is declared with `@contextmanager` and yields a callback handler.
- `libs/core/langchain_core/callbacks/usage.py:L112-L118` — the function creates and registers `usage_metadata_callback_var`, sets it to `cb`, yields `cb`, and clears it only in the statement after the yield.
- `libs/core/langchain_core/callbacks/usage.py:L115-L119` — there is no `try`/`finally` around the yield, so `usage_metadata_callback_var.set(None)` is not guaranteed during exceptional exit.
- `libs/core/tests/unit_tests/callbacks/test_usage_callback.py:L66-L75` — existing tests cover normal context-manager tracking, not exceptional cleanup.

## Finding

Issue Confirmed. The cleanup statement is unreachable when the body raises, leaving the callback registered in the current context. The issue identifies the root cause rather than merely a symptom.

## Recommended Change

Store the `ContextVar` token, wrap `yield cb` in `try`/`finally`, and reset the token in `finally`. Add a regression test that raises inside the context and verifies a subsequent invocation is not tracked.

## Confidence

97%

## Proceed

Yes

