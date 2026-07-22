# Release Documentation Capture

Purpose: Capture TBD documentation for each release.

Triggers:

- Use when a release requires durable local documentation guidance.

Invocation Type: user-invoked

Inputs:

- The release documentation URL and destination notes directory.

Ordered Method:

1. Read the authoritative release documentation and destination rules.
2. Capture the source-backed commands and decisions for future maintenance.

Decisions:

- Prefer the authoritative release documentation over an unverified summary.

Constraints:

- Do not leave TBD values in the derived guidance.

Failure Modes:

- Block if TODO values remain in final documentation.

Outputs:

- A release guidance note with source provenance.

Verification:

- Confirm the release guidance retains its authoritative source link.
