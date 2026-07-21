# Engineering Review

## Issue

openai/openai-python#3516 — Azure `api-key` header is forwarded across cross-origin redirects.

## Summary

The SDK enables redirect following by default and injects Azure API credentials through a custom `api-key` header. The repository evidence supports the issue's defense-in-depth concern: the SDK delegates redirect behavior to httpx while placing a sensitive non-`Authorization` credential on requests.

## Evidence

- `src/openai/_base_client.py:L835-L839` — `DefaultHttpxClient` sets `follow_redirects` to `True` unless callers override it.
- `src/openai/_base_client.py:L1027-L1031` — request construction passes an explicit redirect option through to httpx when supplied; no SDK-specific custom-header redirect policy is applied in this path.
- `src/openai/lib/azure.py:L382-L386` — Azure authentication adds `api-key` when an API key is configured and the request does not already provide that header.
- `src/openai/lib/azure.py:L52-L53` — the SDK recognizes both `Authorization` and `api-key` as Azure authentication headers.

## Finding

Issue Confirmed. The code establishes the prerequisite asymmetry: redirects are followed and Azure credentials use a custom authentication header. The issue's stated cross-origin forwarding behavior belongs to httpx redirect handling, but the SDK's own configuration makes that behavior security-relevant.

## Recommended Change

Disable automatic redirects for Azure API-key requests, or install redirect-aware request handling that removes `api-key` when the origin changes. Add a regression test with two origins and assert that the redirected request does not contain `api-key`.

## Confidence

94%

## Proceed

Yes

