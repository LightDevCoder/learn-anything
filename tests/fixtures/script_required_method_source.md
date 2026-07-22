# Scripted Documentation Capture Method

Purpose: Capture a documentation snapshot reproducibly when a deterministic script is required.

Triggers:

- Use when manually copying a documentation page would omit generated content or repeated normalization.

Invocation Type: model-invoked

Inputs:

- The authoritative URL and a writable snapshot destination.

Ordered Method:

1. Read the target repository rules and confirm the authoritative URL.
2. Run `python scripts/capture_docs.py --url <authoritative-url> --output docs/snapshot.md`.
3. Review the generated snapshot against the authoritative page.

Decisions:

- Use the script because deterministic normalization is required for repeatable snapshots.

Constraints:

- Do not replace the original source page or silently change the script arguments.

Failure Modes:

- Block if `scripts/capture_docs.py` is unavailable or the output path is unwritable.

Outputs:

- A normalized documentation snapshot at `docs/snapshot.md`.

Resources:

- `scripts/capture_docs.py`: required deterministic capture and normalization script.

Verification:

- Confirm `python scripts/capture_docs.py --url <authoritative-url> --output docs/snapshot.md` exits successfully.
- Confirm `docs/snapshot.md` retains the authoritative URL.
