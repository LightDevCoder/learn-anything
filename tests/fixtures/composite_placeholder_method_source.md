# Source Under Review

Purpose: TBD - decide later

Triggers:

- Use when a documentation capture method is required repeatedly.

Invocation Type: user-invoked

Inputs:

- The authoritative URL and destination rules.

Ordered Method:

1. Read the authoritative source.
2. Capture the source-backed operational details.

Decisions:

- Prefer the official source over third-party summaries.

Constraints:

- Do not modify the original source.

Failure Modes:

- Block if the source is unavailable.

Outputs:

- A derived guidance note with provenance.

Resources:

- scripts/capture_docs.py: TBD

Verification:

- Confirm the guidance retains the source link.
