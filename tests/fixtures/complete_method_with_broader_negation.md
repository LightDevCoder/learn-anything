# Durable Documentation Capture

Purpose: Capture durable documentation guidance for future maintenance.

## Scope

This is not merely a one-off and is no longer a one-off; it is not merely a passive summary but a durable maintenance method.

Triggers:

- Use when an official documentation update must become durable local guidance.

Invocation Type: user-invoked

Inputs:

- The official documentation URL and the existing local rules.

Ordered Method:

1. Read the official source and the destination rules before drafting guidance.
2. Record source-backed commands and paths that affect future maintenance.
3. Write the derived guidance without modifying the source.

Decisions:

- Prefer the official source when a third-party summary conflicts with it.

Constraints:

- Preserve the source link and do not invent undocumented steps.

Failure Modes:

- Block until an authoritative source is available for a conflict.

Outputs:

- A local guidance note with source provenance and operational details.

Verification:

- Confirm the guidance retains the source link and exact affected paths.
