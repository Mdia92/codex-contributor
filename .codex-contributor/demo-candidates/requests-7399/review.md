# Engineering Review

## Issue

psf/requests#7399 — `Session.request(verify=...)` documentation duplicates `requests.request()` where behavior differs.

## Summary

`Session.merge_environment_settings` treats `verify=True` and `verify=None` differently before merging with the session's configured `verify` value. This supports the issue's claim that an omitted method argument can preserve session configuration while an explicit `True` can replace it.

## Evidence

- `src/requests/sessions.py:L831-L838` — `merge_environment_settings` accepts `verify` as `VerifyType | None`.
- `src/requests/sessions.py:L844-L860` — when environment trust is enabled, `verify is True or verify is None` may be replaced by a CA-bundle environment setting.
- `src/requests/sessions.py:L862-L868` — `verify = merge_setting(verify, self.verify)` merges the method argument with the session setting; `None` therefore has different merge semantics from an explicit boolean.
- `docs/user/advanced.rst:L248-L252` — documentation states that `verify` defaults to `True`, without explaining the Session-level merge distinction.

## Finding

Issue Confirmed. The issue identifies a documentation precision problem: the method's effective behavior depends on whether `verify` is omitted (`None`) or explicitly set and on the session/environment values that are merged afterward.

## Recommended Change

Document `Session.request` separately from module-level `requests.request`, state that an omitted `verify` defers to session configuration, and add examples covering explicit `True`, explicit `False`, a CA path, and no argument.

## Confidence

91%

## Proceed

Yes

