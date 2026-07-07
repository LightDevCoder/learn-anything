---
name: learn-anything
description: Turn conversations, transcripts, project notes, folder workflows, documentation, or other sources into reusable Codex skills. Use when the user asks to create, update, distill, or "learn" a workflow as a skill; asks to preserve repeated operating methods for future agents; provides corrections/failure modes that should become durable procedure; or wants arbitrary source material transformed into Skill Creator compatible skill instructions.
---

# Learn Anything

## Purpose

Use this skill to convert arbitrary source material into a compact, reusable Codex skill. Extract repeatable operating methods, not passive summaries of what happened.

The generated skill should help a future agent perform the work better with less rediscovery. It should preserve triggers, decisions, commands, constraints, failure modes, verification gates, and output contracts that are likely to recur.

## Source Intake

Gather only the source needed to infer a repeatable method:

- User request or goal statement
- Conversation transcript, task notes, issue thread, README, folder tree, test output, or workflow document
- Corrections from the user, especially repeated "do not do X; do Y" guidance
- Commands, paths, file names, APIs, schemas, and exact error strings that future agents must recognize
- Existing skills or project rules that the new skill must align with

If source material is sparse, produce a learning summary or ask for the missing artifact instead of inventing a skill.

## Decision Workflow

1. Identify whether the request is explicit skill creation, reusable workflow extraction, observation for later reuse, or a normal one-off task.
2. Separate durable procedure from incidental task details. Keep what changes future behavior; drop narration that only explains the past.
3. Extract trigger conditions from user wording and source context. Put all "when to use" information in the generated skill description, not only in the body.
4. Convert corrections and failure modes into constraints, guardrails, or verification checks.
5. Convert repeated commands or fragile operations into bundled scripts only when deterministic execution is useful.
6. Draft the generated skill with Skill Creator conventions.
7. Validate the draft by checking frontmatter, trigger specificity, workflow usefulness, constraints, output format, and quality checks.

## Generated Skill Shape

Every generated skill must include:

- `SKILL.md` with YAML frontmatter containing only `name` and `description`
- A kebab-case folder and skill name under 64 characters
- A description that states both what the skill does and when Codex should use it
- A body written as direct operating instructions
- Sections or equivalent content covering purpose, trigger, inputs, workflow, constraints, output format, and quality checks
- Bundled resources only when they are directly useful

Prefer this body structure unless the source strongly suggests another concise shape:

```markdown
# Skill Title

## Purpose

State what repeatable work the skill enables.

## Inputs

List source artifacts, credentials, paths, or context needed before acting.

## Workflow

Give the minimum ordered procedure that a future agent should follow.

## Constraints

Capture user preferences, scope boundaries, failure modes, safety rules, and exact decisions.

## Output Format

Describe the artifact, summary, patch, command output, or decision the skill should produce.

## Quality Checks

List concrete verification gates before final response.
```

## Extraction Rules

- Preserve exact commands, file names, headings, APIs, error strings, and user corrections when they carry operational meaning.
- Prefer imperative workflow steps over descriptive prose.
- Keep examples short and concrete.
- Do not include project-specific names unless they are necessary trigger signals, path conventions, or examples.
- Do not turn a one-off answer, translation, weather lookup, or time check into a skill.
- Do not create broad memory summaries. Encode how to act differently next time.
- Do not include stub sections, unresolved questions, or unused resource folders.

## Hook Scripts

Optional deterministic helpers live in `hooks/`:

- `learn_gate.py`: classify a request before the task as `normal_task`, `observe_and_summarize`, or `create_or_update_skill`.
- `session_reflector.py`: inspect a completed transcript for reusable learning and return `ignore`, `summarize_candidate`, or `create_skill`.
- `skill_candidate_builder.py`: build a deterministic skill candidate JSON object from source text.

Run them with raw text or a JSON object on stdin. They print JSON so other agents can use the decision without parsing prose.

## Quality Checks

Before delivering a generated or updated skill:

- Confirm `SKILL.md` has valid frontmatter with only `name` and `description`.
- Confirm the description contains concrete trigger conditions.
- Confirm the body teaches a repeatable operating method rather than summarizing a session.
- Confirm constraints reflect user corrections and known failure modes.
- Confirm output format and quality checks are actionable.
- Run Skill Creator validation when a skill folder is available.
