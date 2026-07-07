from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "learn-anything" / "hooks"
FIXTURES = ROOT / "tests" / "fixtures"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, HOOKS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


learn_gate = load_module("learn_gate")
session_reflector = load_module("session_reflector")
skill_candidate_builder = load_module("skill_candidate_builder")


class LearnGateTests(unittest.TestCase):
    def test_explicit_chinese_skill_request_creates_or_updates_skill(self) -> None:
        result = learn_gate.classify({"request": "请把这个工作流创建 skill，沉淀流程给未来 Agent 复用。"})
        self.assertEqual(result["decision"], "create_or_update_skill")
        self.assertGreaterEqual(result["confidence"], 0.8)

    def test_one_off_translation_time_weather_stays_normal(self) -> None:
        cases = [
            "Translate this sentence into English: 你好。",
            "What time is it now?",
            "今天纽约天气怎么样？",
        ]
        for text in cases:
            with self.subTest(text=text):
                result = learn_gate.classify({"request": text})
                self.assertEqual(result["decision"], "normal_task")
                self.assertGreaterEqual(result["confidence"], 0.85)

    def test_folder_project_workflow_observes_and_summarizes(self) -> None:
        result = learn_gate.classify(
            {
                "request": "请观察 C:\\repo\\Learning 项目文件夹里的工作流，整理未来 Agent 可复用的规则和流程。",
                "context": "- read AGENTS.md\n- compare folder names\n- run validation",
            }
        )
        self.assertEqual(result["decision"], "observe_and_summarize")
        self.assertGreaterEqual(result["confidence"], 0.65)

    def test_sparse_noisy_input_is_low_confidence_safe_output(self) -> None:
        result = learn_gate.classify({"request": "?? skill maybe"})
        self.assertEqual(result["decision"], "normal_task")
        self.assertLess(result["confidence"], 0.4)


class SessionReflectorTests(unittest.TestCase):
    def test_transcript_with_corrections_becomes_candidate(self) -> None:
        transcript = (FIXTURES / "transcript_with_corrections.txt").read_text(encoding="utf-8")
        result = session_reflector.reflect({"transcript": transcript})
        self.assertIn(result["decision"], {"summarize_candidate", "create_skill"})
        self.assertGreaterEqual(result["confidence"], 0.65)
        self.assertIn("corrections", " ".join(result["reasons"]))

    def test_sparse_transcript_is_ignored_safely(self) -> None:
        result = session_reflector.reflect({"transcript": "ok fixed"})
        self.assertEqual(result["decision"], "ignore")
        self.assertLess(result["confidence"], 0.4)


class SkillCandidateBuilderTests(unittest.TestCase):
    def test_end_to_end_source_to_skill_candidate(self) -> None:
        source = (FIXTURES / "sample_source.md").read_text(encoding="utf-8")
        result = skill_candidate_builder.build_candidate({"source": source})

        self.assertEqual(result["name"], "browser-docs-capture-workflow")
        self.assertRegex(result["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertIn("website", result["trigger_description"])
        self.assertGreaterEqual(len(result["workflow"]), 4)
        self.assertGreaterEqual(len(result["constraints"]), 2)
        self.assertGreaterEqual(len(result["quality_checks"]), 2)
        self.assertIn("## Workflow", result["skill_md"])
        self.assertIn("## Constraints", result["skill_md"])
        self.assertIn("## Quality Checks", result["skill_md"])
        draft_marker_pattern = "TO" + "DO|place" + "holder"
        self.assertIsNone(re.search(draft_marker_pattern, result["skill_md"], flags=re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
