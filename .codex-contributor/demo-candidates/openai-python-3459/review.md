# Engineering Review

## Issue

openai/openai-python#3459 — `parse_response` crashes when `response.output` is `None`.

## Summary

The parser directly iterates `response.output`. A null output received from an incomplete, proxy, or nonconforming backend will therefore raise `TypeError` inside parsing rather than yielding an empty parsed output.

## Evidence

- `src/openai/lib/_parsing/_responses.py:L53-L61` — `parse_response` initializes `output_list` and then directly executes `for output in response.output` with no null guard.
- `src/openai/types/responses/response.py:L238-L242` — the typed SDK contract describes `Response.output` as a list of generated content items.
- `src/openai/lib/streaming/responses/_responses.py:L360-L365` — streaming completion routes the accumulated response through `parse_response`, so the unguarded loop is on the streaming completion path named in the issue.

## Finding

Issue Confirmed. The public typed contract expects a list, but the parser has no defensive boundary when a backend supplies null. The issue correctly identifies a crash surface; it is not a normal success-response path, but it is a recoverability gap for malformed or incomplete responses.

## Recommended Change

Iterate over `response.output or []` and add a streaming regression test that completes a response with null output, asserting a parsed response with no output items rather than an internal `TypeError`.

## Confidence

96%

## Proceed

Yes

