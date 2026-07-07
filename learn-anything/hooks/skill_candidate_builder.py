#!/usr/bin/env python3
"""Build a deterministic Skill Creator compatible skill candidate from source text."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_WORKFLOW = [
    "Identify the source artifacts and the user's requested reusable outcome.",
    "Extract repeatable decisions, commands, constraints, and verification gates.",
    "Separate durable operating method from one-off project narration.",
    "Draft a compact Skill Creator compatible SKILL.md with concrete trigger metadata.",
    "Validate the draft against frontmatter, trigger, workflow, constraints, output format, and quality checks.",
]

DEFAULT_CONSTRAINTS = [
    "Extract repeatable operating methods, not passive summaries.",
    "Preserve exact commands, paths, APIs, filenames, and error strings when they change future behavior.",
    "Do not invent missing workflow details from sparse source material.",
    "Keep generated skill names kebab-case and under 64 characters.",
]

DEFAULT_QUALITY_CHECKS = [
    "Frontmatter contains only name and description.",
    "Description states both what the skill does and when to use it.",
    "Workflow steps are imperative and repeatable.",
    "Constraints include relevant corrections or failure modes from the source.",
    "No unresolved draft markers remain.",
]


def _read_input(argv_text: list[str], source_file: str | None) -> dict[str, Any]:
    if source_file:
        text = Path(source_file).read_text(encoding="utf-8")
        return {"source": text}

    if argv_text:
        text = " ".join(argv_text)
    else:
        text = sys.stdin.read()

    text = text.strip()
    if not text:
        return {"source": ""}

    if Path(text).exists() and Path(text).is_file():
        text = Path(text).read_text(encoding="utf-8")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"source": text}

    if isinstance(data, dict):
        return data
    return {"source": str(data)}


def _combined_source(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("source", "transcript", "notes", "request", "context"):
        value = data.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif value is not None:
            parts.append(json.dumps(value, ensure_ascii=False))
    return "\n".join(parts).strip()


def kebab_case(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        value = "learned-workflow"
    if len(value) > 63:
        value = value[:63].rstrip("-")
    return value


def _title_from_source(source: str, explicit_name: str | None) -> str:
    if explicit_name:
        return explicit_name.strip()

    title_patterns = [
        r"^\s*#\s+(.+?)\s*$",
        r"^\s*(?:title|name|workflow|skill)\s*:\s*(.+?)\s*$",
        r"^\s*(.+? workflow)\s*$",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _clean_title(match.group(1))

    first_line = next((line.strip() for line in source.splitlines() if line.strip()), "Learned Workflow")
    words = re.findall(r"[A-Za-z0-9]+", first_line)
    if len(words) >= 2:
        return " ".join(words[:6])
    return "Learned Workflow"


def _clean_title(title: str) -> str:
    title = re.sub(r"^[#*\-\d.\s]+", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title or "Learned Workflow"


def _extract_section(source: str, heading: str) -> list[str]:
    pattern = rf"^\s*(?:#+\s*)?{re.escape(heading)}\s*:?\s*$"
    match = re.search(pattern, source, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return []
    rest = source[match.end() :]
    stop = re.search(r"^\s*(?:#+\s*)?[A-Z][A-Za-z ]{2,}\s*:?\s*$", rest, flags=re.MULTILINE)
    block = rest[: stop.start()] if stop else rest
    return _list_items(block)


def _list_items(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        match = re.match(r"^(?:[-*]|\d+[.)])\s+(.+)$", stripped)
        if match:
            items.append(_sentence(match.group(1)))
    return items


def _extract_workflow(source: str) -> list[str]:
    workflow = _extract_section(source, "Workflow") or _extract_section(source, "Steps") or _extract_section(source, "Process")
    if workflow:
        return workflow[:8]

    items = _list_items(source)
    if items:
        return items[:8]

    return DEFAULT_WORKFLOW


def _extract_constraints(source: str) -> list[str]:
    constraints = _extract_section(source, "Constraints") or _extract_section(source, "Rules")
    corrections = []
    for line in source.splitlines():
        stripped = line.strip()
        if re.match(r"^(?:use when|trigger|description)\s*:", stripped, flags=re.IGNORECASE):
            continue
        if re.search(r"\b(?:do not|never|instead|must|avoid)\b|不要|必须|而是|失败|错误", stripped, flags=re.IGNORECASE):
            corrections.append(_sentence(re.sub(r"^(?:[-*]|\d+[.)])\s+", "", stripped)))
    combined = constraints + [item for item in corrections if item not in constraints]
    return (combined or DEFAULT_CONSTRAINTS)[:8]


def _extract_quality_checks(source: str) -> list[str]:
    checks = _extract_section(source, "Quality Checks") or _extract_section(source, "Verification") or _extract_section(source, "Tests")
    return (checks or DEFAULT_QUALITY_CHECKS)[:8]


def _extract_output_format(source: str) -> str:
    patterns = [
        r"^\s*(?:output format|output|deliverable)\s*:\s*(.+?)\s*$",
        r"^\s*##\s*Output Format\s*\n(.+?)(?:\n##|\Z)",
    ]
    for pattern in patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            text = re.sub(r"\s+", " ", match.group(1)).strip()
            if text:
                return _sentence(text[:300])
    return "Return the generated or updated skill files plus a concise verification summary."


def _extract_trigger(source: str, title: str) -> str:
    patterns = [
        r"^\s*(?:use when|trigger|when to use)\s*:\s*(.+?)\s*$",
        r"^\s*description\s*:\s*(.+?)\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            trigger = _sentence(match.group(1))
            if len(trigger.split()) >= 5:
                return trigger
    return f"Use when an AI agent needs to repeat the {title} method from source notes, transcripts, project files, or user corrections."


def _sentence(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" -")
    if not value:
        return value
    if value[-1] not in ".!?":
        value += "."
    return value


def build_candidate(data: dict[str, Any]) -> dict[str, Any]:
    source = _combined_source(data)
    title = _title_from_source(source, data.get("name") if isinstance(data.get("name"), str) else None)
    name = kebab_case(title)
    trigger = _extract_trigger(source, title)
    workflow = _extract_workflow(source)
    constraints = _extract_constraints(source)
    quality_checks = _extract_quality_checks(source)
    output_format = _extract_output_format(source)

    description = f"{_sentence(trigger)} Use when this repeatable workflow should be applied, taught, validated, or encoded for future AI agents."

    skill_md = _render_skill_md(
        name=name,
        title=title,
        description=description,
        trigger=trigger,
        workflow=workflow,
        constraints=constraints,
        quality_checks=quality_checks,
        output_format=output_format,
    )

    return {
        "name": name,
        "title": title,
        "trigger_description": trigger,
        "workflow": workflow,
        "constraints": constraints,
        "output_format": output_format,
        "quality_checks": quality_checks,
        "skill_md": skill_md,
        "confidence": _confidence(source, workflow, constraints, quality_checks),
    }


def _render_skill_md(
    *,
    name: str,
    title: str,
    description: str,
    trigger: str,
    workflow: list[str],
    constraints: list[str],
    quality_checks: list[str],
    output_format: str,
) -> str:
    workflow_lines = "\n".join(f"{idx}. {step}" for idx, step in enumerate(workflow, start=1))
    constraint_lines = "\n".join(f"- {item}" for item in constraints)
    check_lines = "\n".join(f"- {item}" for item in quality_checks)
    return f"""---
name: {name}
description: {description}
---

# {title}

## Purpose

Use this skill to apply a repeatable operating method extracted from source material.

## Trigger

{_sentence(trigger)}

## Inputs

- Source artifacts or user context needed to run the workflow.
- Relevant paths, commands, corrections, examples, or failure modes.

## Workflow

{workflow_lines}

## Constraints

{constraint_lines}

## Output Format

{_sentence(output_format)}

## Quality Checks

{check_lines}
"""


def _confidence(source: str, workflow: list[str], constraints: list[str], checks: list[str]) -> float:
    score = 0.35
    if len(source) > 200:
        score += 0.15
    if workflow and workflow != DEFAULT_WORKFLOW:
        score += 0.2
    if constraints and constraints != DEFAULT_CONSTRAINTS:
        score += 0.15
    if checks and checks != DEFAULT_QUALITY_CHECKS:
        score += 0.1
    return round(min(score, 0.95), 2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="*", help="Raw source text, JSON, or a file path")
    parser.add_argument("--source-file", help="Path to source text")
    args = parser.parse_args()

    result = build_candidate(_read_input(args.text, args.source_file))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
