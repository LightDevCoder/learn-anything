# Release incident recap

Yesterday I repaired a single release after a malformed changelog stopped the job.
I ran `corepack pnpm@9.15.4 test`, changed `C:\repo\release\CHANGELOG.md`, and reran the job.
This incident was unique to release 4.2 and no repeatable procedure, trigger, or future use was identified.
