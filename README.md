# Skill-Learn-anything

`learn-anything` is a portable agent meta-skill for turning conversations, transcripts, project notes, folder workflows, documentation, or other source material into reusable Skill Creator compatible skills.

The core rule is simple: extract repeatable operating methods, not passive summaries.

## Repository Layout

- `learn-anything/SKILL.md` - the installable agent skill.

Compatible consumers include OpenAI Codex, Claude Code, Gemini CLI, Cursor agents, Windsurf agents, GitHub Copilot coding agent, Aider, OpenCode, Roo Code, Continue, CrewAI, LangGraph, AutoGen, ReAct-style custom agents, and other Markdown-reading coding, research, documentation, or automation agents.
- `learn-anything/hooks/learn_gate.py` - pre-task scoring and mode selection.
- `learn-anything/hooks/session_reflector.py` - post-task reusable-learning detection.
- `learn-anything/hooks/skill_candidate_builder.py` - deterministic source-to-skill candidate builder.
- `learn-anything/hooks/config.example.json` - machine-readable hook decision contract.
- `tests/fixtures/` - simulated sources and transcripts.
- `tests/test_hooks.py` - standard-library tests for all hooks and the end-to-end simulation.

## Verify

Run the hook tests:

```powershell
python -m unittest discover -s tests
```

Run Skill Creator validation:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" learn-anything
```

Run an end-to-end candidate build:

```powershell
python .\learn-anything\hooks\skill_candidate_builder.py --source-file .\tests\fixtures\sample_source.md
```

## Install Locally

Copy or sync `learn-anything` into:

```text
C:\Users\Service01\.codex\skills\learn-anything
```

Then verify the installed `SKILL.md` can be read from that path.
