from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "learn-anything" / "hooks"
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(HOOKS))

import package_builder  # noqa: E402
import skill_candidate_builder  # noqa: E402


def complete_payload() -> dict[str, object]:
    return skill_candidate_builder.build_candidate(
        {"source": (FIXTURES / "complete_method_source.md").read_text(encoding="utf-8")}
    )


class PackageBuilderTests(unittest.TestCase):
    def test_complete_contract_creates_small_installable_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = package_builder.build_package(complete_payload(), temporary)
            package = Path(result["package"])
            skill = (package / "SKILL.md").read_text(encoding="utf-8")

            self.assertEqual(result["outcome"], "created")
            self.assertEqual(result["name"], "browser-docs-capture-method")
            self.assertIn("## Invocation and Boundaries", skill)
            self.assertIn("Invocation type: **user-invoked**", skill)
            self.assertIn("corepack pnpm@9.15.4 test", skill)
            self.assertIn("C:\\repo\\Learning\\AGENTS.md", skill)
            self.assertIn("## Completion Criteria", skill)
            self.assertNotIn("writing-great-skills", skill)
            self.assertFalse((package / "references").exists())

    def test_incomplete_source_is_blocked_before_any_package_write(self) -> None:
        payload = skill_candidate_builder.build_candidate(
            {"source": (FIXTURES / "sparse_source.md").read_text(encoding="utf-8")}
        )
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(package_builder.PackageBuildError):
                package_builder.build_package(payload, temporary)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_placeholder_and_unresolved_gap_contract_is_rejected(self) -> None:
        payload = complete_payload()
        contract = dict(payload["method_contract"])
        contract["unresolved_gaps"] = ["verification"]
        with self.assertRaisesRegex(package_builder.PackageBuildError, "unresolved_gaps"):
            package_builder.validate_contract(contract)

        contract = dict(payload["method_contract"])
        contract["purpose"] = "TBD"
        with self.assertRaisesRegex(package_builder.PackageBuildError, "purpose"):
            package_builder.validate_contract(contract)

    def test_guardrail_mentioning_draft_tokens_is_not_treated_as_missing_evidence(self) -> None:
        payload = json.loads(json.dumps(complete_payload()))
        payload["method_contract"]["constraints"] = ["Do not leave TBD markers in the generated package."]
        payload["method_contract"]["failure_modes"] = ["Fail if TODO markers remain after verification."]
        normalized = package_builder.validate_contract(payload)
        self.assertEqual(normalized["constraints"][0], payload["method_contract"]["constraints"][0])
        self.assertEqual(normalized["failure_modes"][0], payload["method_contract"]["failure_modes"][0])

        blocked = json.loads(json.dumps(complete_payload()))
        blocked["method_contract"]["constraints"] = ["TBD"]
        blocked["method_contract"]["failure_modes"] = ["TODO"]
        with self.assertRaisesRegex(package_builder.PackageBuildError, "constraints"):
            package_builder.validate_contract(blocked)

    def test_update_and_duplicate_noop_boundaries_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = package_builder.build_package(complete_payload(), temporary)
            no_op = package_builder.build_package(complete_payload(), temporary)
            self.assertEqual(first["outcome"], "created")
            self.assertEqual(no_op["outcome"], "no-op")

            changed = json.loads(json.dumps(complete_payload()))
            changed["method_contract"]["purpose"] = "Capture official documentation with a recorded source trail."
            with self.assertRaisesRegex(package_builder.PackageBuildError, "allow_update"):
                package_builder.build_package(changed, temporary)
            updated = package_builder.build_package(changed, temporary, allow_update=True)
            self.assertEqual(updated["outcome"], "updated")
            self.assertIn(
                "recorded source trail",
                (Path(updated["package"]) / "SKILL.md").read_text(encoding="utf-8"),
            )

    def test_update_removes_only_resources_managed_by_the_previous_contract(self) -> None:
        first = json.loads(json.dumps(complete_payload()))
        first["method_contract"]["resources"] = ["scripts/capture_docs.py"]
        second = json.loads(json.dumps(first))
        second["method_contract"]["resources"] = ["none"]
        with tempfile.TemporaryDirectory() as temporary:
            resource_root = Path(temporary) / "resources"
            (resource_root / "scripts").mkdir(parents=True)
            (resource_root / "scripts" / "capture_docs.py").write_text("print('capture')\n", encoding="utf-8")
            built = package_builder.build_package(first, Path(temporary) / "built", resource_root=resource_root)
            package = Path(built["package"])
            (package / "notes.txt").write_text("user-owned\n", encoding="utf-8")
            updated = package_builder.build_package(second, Path(temporary) / "built", allow_update=True)
            self.assertEqual(updated["outcome"], "updated")
            self.assertFalse((package / "scripts" / "capture_docs.py").exists())
            self.assertFalse((package / "scripts").exists())
            self.assertEqual((package / "notes.txt").read_text(encoding="utf-8"), "user-owned\n")
            self.assertEqual(json.loads((package / package_builder.MANAGED_MANIFEST).read_text(encoding="utf-8"))["managed_resources"], [])

            duplicate_root = Path(temporary) / "duplicate"
            duplicate_root.mkdir()
            package_dir = duplicate_root / "browser-docs-capture-method"
            package_dir.mkdir()
            (package_dir / "SKILL.md").write_text("---\nname: browser-docs-capture-method\ndescription: owned\n---\n", encoding="utf-8")
            duplicate = package_builder.build_package(complete_payload(), duplicate_root)
            self.assertEqual(duplicate["outcome"], "duplicate")

    def test_model_invoked_contract_is_explicit_without_user_skill_execution(self) -> None:
        payload = complete_payload()
        payload = json.loads(json.dumps(payload))
        payload["method_contract"]["invocation_type"] = "model-invoked"
        with tempfile.TemporaryDirectory() as temporary:
            result = package_builder.build_package(payload, temporary, name="model-method")
            skill = (Path(result["package"]) / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Invocation type: **model-invoked**", skill)
            self.assertIn("recommend it and wait for the user's choice", skill)

    def test_installation_is_clean_idempotent_and_updateable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            build_root = Path(temporary) / "build"
            install_root = Path(temporary) / "installed"
            built = package_builder.build_package(complete_payload(), build_root)
            source = Path(built["package"])

            installed = package_builder.install_package(source, install_root)
            self.assertEqual(installed["outcome"], "installed")
            self.assertEqual(package_builder.install_package(source, install_root)["outcome"], "no-op")

            changed = source / "SKILL.md"
            changed.write_text(changed.read_text(encoding="utf-8").replace("## Purpose", "## Purpose\n\nGenerated package"), encoding="utf-8")
            self.assertEqual(package_builder.install_package(source, install_root)["outcome"], "duplicate")
            self.assertEqual(package_builder.install_package(source, install_root, allow_update=True)["outcome"], "updated")

    def test_install_update_removes_stale_managed_resource_but_keeps_unmanaged_file(self) -> None:
        first = json.loads(json.dumps(complete_payload()))
        first["method_contract"]["resources"] = ["scripts/capture_docs.py"]
        second = json.loads(json.dumps(first))
        second["method_contract"]["resources"] = ["none"]
        with tempfile.TemporaryDirectory() as temporary:
            resource_root = Path(temporary) / "resources"
            (resource_root / "scripts").mkdir(parents=True)
            (resource_root / "scripts" / "capture_docs.py").write_text("print('capture')\n", encoding="utf-8")
            build_root = Path(temporary) / "build"
            first_package = Path(package_builder.build_package(first, build_root, resource_root=resource_root)["package"])
            install_root = Path(temporary) / "installed"
            package_builder.install_package(first_package, install_root)
            destination = install_root / first_package.name
            (destination / "user-owned.txt").write_text("keep\n", encoding="utf-8")

            second_root = Path(temporary) / "build-second"
            second_package = Path(package_builder.build_package(second, second_root)["package"])
            self.assertEqual(package_builder.install_package(second_package, install_root)["outcome"], "duplicate")
            self.assertEqual(package_builder.install_package(second_package, install_root, allow_update=True)["outcome"], "updated")
            self.assertFalse((destination / "scripts" / "capture_docs.py").exists())
            self.assertEqual((destination / "user-owned.txt").read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(package_builder.install_package(second_package, install_root)["outcome"], "no-op")

    def test_declared_resources_are_referenced_without_fabricating_files(self) -> None:
        payload = json.loads(json.dumps(complete_payload()))
        payload["method_contract"]["resources"] = ["scripts/capture_docs.py"]
        with tempfile.TemporaryDirectory() as temporary:
            resource_root = Path(temporary) / "resources"
            (resource_root / "scripts").mkdir(parents=True)
            (resource_root / "scripts" / "capture_docs.py").write_text("print('capture')\n", encoding="utf-8")
            result = package_builder.build_package(payload, Path(temporary) / "built", resource_root=resource_root)
            package = Path(result["package"])
            skill = (package / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("`scripts/capture_docs.py`", skill)
            self.assertEqual((package / "scripts" / "capture_docs.py").read_text(encoding="utf-8"), "print('capture')\n")

    def test_missing_relative_resource_blocks_without_creating_package(self) -> None:
        payload = json.loads(json.dumps(complete_payload()))
        payload["method_contract"]["resources"] = ["scripts/missing.py"]
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(package_builder.PackageBuildError, "resource"):
                package_builder.build_package(payload, temporary, resource_root=Path(temporary) / "resources")
            self.assertEqual(list(Path(temporary).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
