# Fenced Command Verification Method

Purpose: Verify a repeatable documentation update with the source-provided test command.

Triggers:

- Use when a documentation update needs a deterministic verification step.

Invocation Type: user-invoked

Inputs:

- The changed documentation and repository test environment.

Ordered Method:

1. Review the changed documentation against its authoritative source.
2. Run the source-provided test command.
3. Record the verification result with the documentation update.

Decisions:

- Keep the exact source-provided test command instead of substituting a generic check.

Constraints:

- Do not alter the command arguments from the source material.

Failure Modes:

- Block if the test command fails or is unavailable.

Outputs:

- A verified documentation update with recorded command evidence.

Resources:

- none

Verification:

```bash
corepack pnpm@9.15.4 test
```
