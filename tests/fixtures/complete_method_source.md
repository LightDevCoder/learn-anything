# Browser Docs Capture Method

Purpose: Capture authoritative browser documentation as durable local guidance for future agents.

Triggers:

- Use when an agent must turn a product manual or official documentation page into repeatable local guidance.

Invocation Type: user-invoked

Inputs:

- The authoritative URL and the target local notes directory.
- Existing `AGENTS.md` instructions in `C:\repo\Learning`.

Ordered Method:

1. Open the authoritative source and record its exact URL, title, and relevant headings.
2. Read `C:\repo\Learning\AGENTS.md` before creating a derived note.
3. Capture exact commands, paths, options, and errors that change future behavior.
4. Run `corepack pnpm@9.15.4 test` after the derived guidance is written.

Decisions:

- Prefer the official manual over a third-party summary when both describe the same procedure.
- Keep the result user-invoked because creating durable local guidance requires intentional user approval.

Constraints:

- Do not replace the original source file; preserve it alongside the derived guidance.
- Do not invent steps that are absent from the authoritative source.

Failure Modes:

- The capture fails if a third-party summary replaces the official manual without recording the substitution.
- The capture is blocked when `C:\repo\Learning\AGENTS.md` is unavailable or contradicts the requested destination.

Outputs:

- A derived local guidance note with its authoritative source link and exact operational details.

Resources:

- `C:\repo\Learning\AGENTS.md`: mandatory local rules for the destination.

Verification:

- Confirm the original source remains unchanged.
- Confirm `corepack pnpm@9.15.4 test` exits successfully.

Correction:

- Do not omit the docs capture command; keep `corepack pnpm@9.15.4 test` exactly as written.
