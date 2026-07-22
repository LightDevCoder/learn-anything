from __future__ import annotations

import importlib.util
import json
import subprocess
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
    def _run_builder(self, source: str | None = None, source_file: Path | None = None) -> dict[str, object]:
        command = [sys.executable, str(HOOKS / "skill_candidate_builder.py")]
        if source_file:
            command.extend(["--source-file", str(source_file)])
        completed = subprocess.run(
            command,
            input=source,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_complete_authoritative_method_returns_internal_contract_and_preserves_evidence(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "complete_method_source.md")

        self.assertEqual(result["outcome"], "method_contract")
        self.assertEqual(result["promotion_status"], "eligible_for_package_build")
        self.assertNotIn("skill_md", result)

        contract = result["method_contract"]
        self.assertTrue(
            {
                "purpose",
                "triggers",
                "invocation_type",
                "inputs",
                "ordered_method",
                "decisions",
                "constraints",
                "failure_modes",
                "outputs",
                "resources",
                "verification",
                "unresolved_gaps",
                "confidence",
            }.issubset(contract)
        )
        self.assertEqual(contract["invocation_type"], "user-invoked")
        self.assertGreaterEqual(len(contract["ordered_method"]), 4)
        self.assertGreaterEqual(len(contract["decisions"]), 1)
        self.assertGreaterEqual(len(contract["failure_modes"]), 1)
        self.assertEqual(contract["unresolved_gaps"], [])
        self.assertIn("corepack pnpm@9.15.4 test", "\n".join(contract["source_evidence"]["commands"]))
        self.assertIn("C:\\repo\\Learning", "\n".join(contract["source_evidence"]["paths"]))
        self.assertIn("docs capture command", "\n".join(contract["source_evidence"]["corrections"]).lower())
        self.assertIn("third-party summary replaces", "\n".join(contract["source_evidence"]["failure_modes"]))
        self.assertGreaterEqual(contract["confidence"], 0.8)

    def test_one_off_narration_returns_not_promoted_learning_summary(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "one_off_incident.md")

        self.assertEqual(result["outcome"], "learning_summary")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertNotIn("method_contract", result)
        self.assertNotIn("skill_md", result)
        self.assertIn("one-off", result["reason"].lower())
        self.assertIn("corepack pnpm@9.15.4 test", result["learning_summary"]["preserved_details"]["commands"])

    def test_passive_summary_is_not_promoted_to_a_skill(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "passive_summary.md")

        self.assertEqual(result["outcome"], "learning_summary")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertNotIn("method_contract", result)
        self.assertNotIn("skill_md", result)
        self.assertIn("passive", result["reason"].lower())

    def test_sparse_source_is_blocked_with_precise_gaps_and_no_generic_skill(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "sparse_source.md")

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertNotIn("method_contract", result)
        self.assertNotIn("skill_md", result)
        self.assertEqual(
            result["missing_information"],
            [
                "purpose",
                "triggers",
                "invocation_type",
                "inputs",
                "ordered_method",
                "decisions",
                "constraints",
                "failure_modes",
                "outputs",
                "verification",
            ],
        )
        self.assertIn("invocation_type", result["required_source_gaps"])

    def test_placeholder_and_generic_boilerplate_values_block_promotion(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "placeholder_method_source.md")

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertNotIn("method_contract", result)
        self.assertNotIn("skill_md", result)
        self.assertEqual(
            result["missing_information"],
            [
                "purpose",
                "triggers",
                "invocation_type",
                "inputs",
                "ordered_method",
                "decisions",
                "constraints",
                "failure_modes",
                "outputs",
                "verification",
            ],
        )
        self.assertIn("TBD", result["placeholder_source_values"]["purpose"])
        self.assertIn("Describe the decision rules here.", result["placeholder_source_values"]["decisions"])

    def test_composite_placeholders_and_unresolved_resources_block_promotion(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "composite_placeholder_method_source.md")

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertNotIn("method_contract", result)
        self.assertEqual(result["missing_information"], ["purpose", "resources"])
        self.assertIn("TBD - decide later", result["placeholder_source_values"]["purpose"])
        self.assertIn("scripts/capture_docs.py: TBD", result["placeholder_source_values"]["resources"])

    def test_inline_placeholder_markup_in_required_field_blocks_promotion(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "inline_placeholder_markup_method_source.md")

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertNotIn("method_contract", result)
        self.assertEqual(result["missing_information"], ["purpose"])
        self.assertIn("<placeholder>", "\n".join(result["placeholder_source_values"]["purpose"]))

    def test_inline_tbd_token_in_method_defining_field_blocks_promotion(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "inline_tbd_method_source.md")

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertNotIn("method_contract", result)
        self.assertEqual(result["missing_information"], ["purpose"])
        self.assertIn("Capture TBD documentation", "\n".join(result["placeholder_source_values"]["purpose"]))

    def test_complete_method_with_negated_one_off_language_is_not_demoted(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "complete_method_with_safe_narration.md")

        self.assertEqual(result["outcome"], "method_contract")
        self.assertEqual(result["source_kind"], "reusable_method")

    def test_complete_method_with_no_procedure_failure_mode_is_not_demoted(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "complete_method_with_safe_narration.md")

        self.assertEqual(result["outcome"], "method_contract")
        self.assertIn("no procedure", "\n".join(result["method_contract"]["failure_modes"]).lower())

    def test_broader_negated_one_off_and_passive_language_in_scope_is_not_demoted(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "complete_method_with_broader_negation.md")

        self.assertEqual(result["outcome"], "method_contract")
        self.assertEqual(result["source_kind"], "reusable_method")

    def test_scope_one_off_signal_is_not_promoted(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "scope_one_off_method_source.md")

        self.assertEqual(result["outcome"], "learning_summary")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertEqual(result["source_kind"], "one_off_narration")
        self.assertNotIn("method_contract", result)

    def test_structured_affirmative_one_off_method_is_not_promoted(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "structured_one_off_method_source.md")

        self.assertEqual(result["outcome"], "learning_summary")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertEqual(result["source_kind"], "one_off_narration")
        self.assertNotIn("method_contract", result)
        self.assertNotIn("skill_md", result)

    def test_structured_passive_summary_is_not_promoted(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "structured_passive_summary_source.md")

        self.assertEqual(result["outcome"], "learning_summary")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertEqual(result["source_kind"], "passive_summary")
        self.assertNotIn("method_contract", result)
        self.assertNotIn("skill_md", result)

    def test_script_required_source_preserves_resource_in_internal_contract(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "script_required_method_source.md")

        self.assertEqual(result["outcome"], "method_contract")
        self.assertIn("scripts/capture_docs.py", "\n".join(result["method_contract"]["resources"]))
        self.assertIn("python scripts/capture_docs.py", "\n".join(result["method_contract"]["source_evidence"]["commands"]))

    def test_fenced_command_is_preserved_in_internal_contract_evidence(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "fenced_command_method_source.md")

        self.assertEqual(result["outcome"], "method_contract")
        self.assertIn("corepack pnpm@9.15.4 test", result["method_contract"]["source_evidence"]["commands"])
        self.assertEqual(result["method_contract"]["resources"], ["none"])

    def test_explicit_model_invocation_is_preserved_in_the_contract(self) -> None:
        source = (FIXTURES / "complete_method_source.md").read_text(encoding="utf-8")
        result = self._run_builder(source.replace("Invocation Type: user-invoked", "Invocation Type: model-invoked"))

        self.assertEqual(result["outcome"], "method_contract")
        self.assertEqual(result["method_contract"]["invocation_type"], "model-invoked")

    def test_conflicting_invocation_evidence_blocks_promotion(self) -> None:
        result = self._run_builder(source_file=FIXTURES / "conflicting_invocation_method_source.md")

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["promotion_status"], "not_promoted")
        self.assertNotIn("method_contract", result)
        self.assertEqual(result["missing_information"], ["invocation_type"])
        self.assertEqual(result["invocation_type_conflict"], ["user-invoked", "model-invoked"])
        self.assertIn("choose exactly one", result["required_source_gaps"]["invocation_type"].lower())


if __name__ == "__main__":
    unittest.main()
