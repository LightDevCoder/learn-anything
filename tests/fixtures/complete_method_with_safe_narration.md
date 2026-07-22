# Durable Documentation Capture

Purpose: This is not a one-off process; it preserves repeatable documentation capture for future maintenance.

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

- The prior capture had no procedure for reconciling a source conflict; block until the authoritative source is available.

Outputs:

- A local guidance note with source provenance and operational details.

Verification:

- Confirm the guidance retains the source link and exact affected paths.
