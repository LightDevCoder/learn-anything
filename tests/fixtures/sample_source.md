# Browser Docs Capture Workflow

Purpose: capture browser-based documentation into reusable local skill guidance.

Use when: Codex must turn a website, product manual, or repository documentation workflow into repeatable skill instructions for future agents.

Workflow:

1. Open the authoritative source and capture the exact URL, title, and relevant headings.
2. Extract only procedures, commands, constraints, and verification checks that change future behavior.
3. Preserve exact commands, paths, option names, and error strings when they are operationally meaningful.
4. Remove passive session narration and one-off project details.
5. Write a concise Skill Creator compatible SKILL.md.
6. Run validation and a small simulated task before delivery.

Constraints:

- Do not summarize the source as general background.
- Prefer primary documentation over third-party summaries.
- Ask before using network access when the environment requires approval.

Quality Checks:

- The generated skill name is kebab-case.
- The trigger description is specific enough for automatic invocation.
- The workflow contains concrete repeatable steps.
- Constraints and quality checks are present.

Output Format: return a candidate skill folder name, SKILL.md content, constraints, and verification notes.
