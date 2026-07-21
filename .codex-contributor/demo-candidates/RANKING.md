# Demo candidate ranking

All five candidates are confirmed findings. No candidate was marked challenged, so ranking uses evidence strength, surprise value, and confidence after the verdict criterion.

| Rank | Candidate | Verdict | Confidence | Evidence strength | Surprise value | Why it ranks here |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | openai/openai-python#3516 | ✓ Confirmed | 94% | 4 cited locations | High | Redirect-following plus a custom Azure credential produces a memorable, security-relevant finding. |
| 2 | langchain-ai/langchain#38989 | ✓ Confirmed | 97% | 4 cited locations | High | A one-line exceptional-cleanup gap creates silent tracking after a scoped block. |
| 3 | openai/openai-python#3459 | ✓ Confirmed | 96% | 3 cited locations | Medium | Clear streaming crash path and a minimal, defensible fix. |
| 4 | pallets/flask#6093 | ✓ Confirmed | 93% | 3 cited locations | Medium | Two independent first-colon splits reveal a shared IPv6 assumption. |
| 5 | psf/requests#7399 | ✓ Confirmed | 91% | 4 cited locations | Medium | Strong documentation/behavior mismatch, but less visually immediate in a demo. |

Recommended hero: **openai/openai-python#3516**.

