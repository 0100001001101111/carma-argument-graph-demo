from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import aletheia_argument_graph.case as case_module
from aletheia_argument_graph import build_case_graph, grounded_semantics, validate_graph


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = build_case_graph(ROOT)

    def test_positive_case(self) -> None:
        self.assertEqual(validate_graph(copy.deepcopy(self.graph)), {"state": "ACCEPT", "errors": []})

    def test_grounded_result(self) -> None:
        result = grounded_semantics(copy.deepcopy(self.graph))
        self.assertIn("claim:verification", result["accepted_with_direct_support"])
        self.assertIn("objection:capability", result["dialectically_rejected"])

    def test_source_hash_mutation(self) -> None:
        graph = copy.deepcopy(self.graph)
        graph["nodes"][0]["source"]["sha256"] = "0" * 64
        self.assertIn("source_hash_mismatch:claim:verification", validate_graph(graph)["errors"])

    def test_manifest_root_mutation(self) -> None:
        old = case_module.EXPECTED_MANIFEST_SHA256
        case_module.EXPECTED_MANIFEST_SHA256 = "0" * 64
        try:
            with self.assertRaisesRegex(ValueError, "manifest root hash mismatch"):
                build_case_graph(ROOT)
        finally:
            case_module.EXPECTED_MANIFEST_SHA256 = old

    def test_self_consistent_score_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            twin = Path(tmp) / "repo"
            (twin / "data/evidence").mkdir(parents=True)
            model_data = json.loads((ROOT / "data/evidence/model_results.json").read_text())
            next(row for row in model_data["results"] if row["id"] == "codex")["blind_hit_trials"] = 0
            model_path = twin / "data/evidence/model_results.json"
            model_path.write_text(json.dumps(model_data, sort_keys=True))
            notes_path = twin / "data/evidence/method_notes.json"
            notes_path.write_bytes((ROOT / "data/evidence/method_notes.json").read_bytes())
            manifest = json.loads((ROOT / "data/source_manifest.json").read_text())
            for row in manifest["sources"]:
                target = model_path if row["id"] == "model_results" else notes_path
                row["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            manifest_path = twin / "data/source_manifest.json"
            manifest_path.write_text(json.dumps(manifest, sort_keys=True))
            old = case_module.EXPECTED_MANIFEST_SHA256
            case_module.EXPECTED_MANIFEST_SHA256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            try:
                with self.assertRaisesRegex(ValueError, "codex extract no longer supports 15 of 25"):
                    build_case_graph(twin)
            finally:
                case_module.EXPECTED_MANIFEST_SHA256 = old

    def test_missing_selected_objection(self) -> None:
        graph = copy.deepcopy(self.graph)
        objection = graph["strongest_objection_id"]
        graph["nodes"] = [node for node in graph["nodes"] if node["id"] != objection]
        graph["edges"] = [edge for edge in graph["edges"] if objection not in {edge["source"], edge["target"]}]
        self.assertIn("missing_selected_objection", validate_graph(graph)["errors"])

    def test_candidate_cannot_support(self) -> None:
        graph = copy.deepcopy(self.graph)
        edge = next(edge for edge in graph["edges"] if edge["source"] == "uncertainty:encoding")
        edge["type"] = "supports"
        self.assertIn(f"candidate_overpromoted:{edge['id']}", validate_graph(graph)["errors"])

    def test_confidence_is_rule_bound(self) -> None:
        graph = copy.deepcopy(self.graph)
        graph["nodes"][0]["confidence"]["level"] = "SOURCE_MATCH"
        self.assertIn("confidence_policy_mismatch:claim:verification", validate_graph(graph)["errors"])

    def test_claim_ceiling_tripwire(self) -> None:
        graph = copy.deepcopy(self.graph)
        next(node for node in graph["nodes"] if node["id"] == graph["top_claim_id"])["text"] = "This system solves scientific discovery."
        self.assertIn("claim_exceeds_ceiling", validate_graph(graph)["errors"])

    def test_dependency_cycle(self) -> None:
        graph = copy.deepcopy(self.graph)
        edge = copy.deepcopy(graph["edges"][0])
        edge.update({"id": "edge:cycle", "source": "assumption:transfer", "target": "claim:verification", "type": "depends_on"})
        graph["edges"].append(edge)
        self.assertIn("depends_on_cycle", validate_graph(graph)["errors"])

    def test_two_runs_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = subprocess.run([sys.executable, str(ROOT / "run_demo.py"), "--output", first], cwd=ROOT, capture_output=True, text=True)
            two = subprocess.run([sys.executable, str(ROOT / "run_demo.py"), "--output", second], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(one.returncode, 0, one.stderr)
            self.assertEqual(two.returncode, 0, two.stderr)
            for name in ("argument_graph.json", "semantics.json", "index.html"):
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
