# Engineering Review

## Issue

pallets/flask#6093 — IPv6 addresses are parsed incorrectly because of `.partition(":")`.

## Summary

Two current code paths split host strings on the first colon. That representation cannot distinguish an IPv6 literal from a host-and-port separator.

## Evidence

- `src/flask/app.py:L720-L728` — `Flask.run` reads `SERVER_NAME` and assigns `sn_host, _, sn_port = server_name.partition(":")` before using `sn_host` as the host.
- `src/flask/testing.py:L176-L183` — `session_transaction` passes `ctx.request.host.partition(":")[0]` into cookie updates.
- `src/flask/app.py:L724-L732` — when `SERVER_NAME` is set and no explicit host is passed, the partition-derived host becomes the run host.

## Finding

Issue Confirmed. Both cited paths use first-colon splitting on values that can contain IPv6 literals. The issue correctly points to a shared parsing assumption rather than unrelated IPv6 failures.

## Recommended Change

Use an IPv6-aware host/port parser that recognizes bracketed literals, preserve the full IPv6 host for `SERVER_NAME`, and add regression tests for `[::1]:8080` in both `Flask.run` and `session_transaction`.

## Confidence

93%

## Proceed

Yes

