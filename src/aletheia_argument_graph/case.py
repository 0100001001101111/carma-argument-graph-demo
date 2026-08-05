"""Build the portable Project Aletheia demonstration case."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_MANIFEST_SHA256 = "e9f1531e0e2436372d40a8c6f075b86cfc9154f055f691b699d9a9b4073e17c8"
TOP_CLAIM = "Frontier AI can sometimes propose a useful scientific reframe, but an individual proposal needs an independent check before it becomes evidence."
CONFIDENCE_BY_STATUS = {
    "DIRECT_SOURCE": "SOURCE_MATCH",
    "VERIFIED_SOURCE": "VERIFIED_METHOD",
    "CANDIDATE_SOURCE": "CANDIDATE",
    "HUMAN_SYNTHESIS": "BOUNDED_SYNTHESIS",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_sources(repo_root: Path) -> dict[str, dict[str, Any]]:
    manifest_path = repo_root / "data/source_manifest.json"
    if _sha256(manifest_path) != EXPECTED_MANIFEST_SHA256:
        raise ValueError("source manifest root hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = {}
    for item in manifest["sources"]:
        path = (repo_root / item["path"]).resolve()
        if _sha256(path) != item["sha256"]:
            raise ValueError(f"source hash mismatch: {item['id']}")
        sources[item["id"]] = {"path": str(path), "sha256": item["sha256"], "data": json.loads(path.read_text(encoding="utf-8"))}
    return sources


def _node(node_id: str, kind: str, text: str, source: dict[str, Any], status: str, basis: str, ceiling: str) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": kind,
        "text": text,
        "source": {"path": source["path"], "sha256": source["sha256"]},
        "validation_status": status,
        "claim_authority": "BOUNDED_PORTABLE_EVIDENCE",
        "confidence": {"level": CONFIDENCE_BY_STATUS[status], "basis": basis},
        "claim_ceiling": ceiling,
    }


def build_case_graph(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = _load_sources(root)
    results = {item["id"]: item for item in sources["model_results"]["data"]["results"]}
    notes = {item["id"]: item for item in sources["method_notes"]["data"]["notes"]}
    expected = {"qwen": (0, 25), "haiku": (0, 25), "codex": (15, 25)}
    for result_id, pair in expected.items():
        result = results[result_id]
        if (result["blind_hit_trials"], result["trials"]) != pair:
            raise ValueError(f"{result_id} extract no longer supports {pair[0]} of {pair[1]}")
    if results["codex"]["null_hit_trials"] != 0:
        raise ValueError("codex null extract changed")
    if notes["j57"]["status"] != "VERIFIED" or notes["c61"]["status"] != "CANDIDATE":
        raise ValueError("method-note status changed")

    ceiling = "Guided rediscovery on one frozen task family. No broad or novel-discovery claim."
    nodes = [
        _node("claim:verification", "claim", TOP_CLAIM, sources["model_results"], "HUMAN_SYNTHESIS", "Bounded synthesis of three model evaluations and two method notes.", ceiling),
        _node("evidence:qwen", "evidence", f"Qwen produced accepted certificates in {results['qwen']['blind_hit_trials']} of {results['qwen']['trials']} frozen trials.", sources["model_results"], "DIRECT_SOURCE", "Re-extracted from the included evidence file.", ceiling),
        _node("evidence:haiku", "evidence", f"Haiku produced accepted certificates in {results['haiku']['blind_hit_trials']} of {results['haiku']['trials']} frozen trials.", sources["model_results"], "DIRECT_SOURCE", "Re-extracted from the included evidence file.", ceiling),
        _node("evidence:codex", "evidence", f"Codex produced accepted certificates in {results['codex']['blind_hit_trials']} of {results['codex']['trials']} frozen trials. The null proposer scored {results['codex']['null_hit_trials']} of {results['codex']['trials']}.", sources["model_results"], "DIRECT_SOURCE", "Re-extracted from the included evidence file.", ceiling),
        _node("assumption:transfer", "assumption", "Behavior on this task family may not transfer to other scientific domains or open-ended discovery.", sources["model_results"], "HUMAN_SYNTHESIS", "Human-selected scope boundary.", ceiling),
        _node("objection:capability", "objection", "The 15 of 25 Codex result shows meaningful guided-rediscovery capability and pushes against an overly skeptical reading.", sources["model_results"], "HUMAN_SYNTHESIS", "Human-selected strongest objection for this case.", ceiling),
        _node("rebuttal:single-output", "rebuttal", "The same Codex run missed 10 of 25 trials, and guided-rediscovery success cannot validate a particular new proposal.", sources["model_results"], "HUMAN_SYNTHESIS", "25 minus 15, with the task boundary preserved.", ceiling),
        _node("evidence:j57", "evidence", notes["j57"]["summary"], sources["method_notes"], "VERIFIED_SOURCE", "Status and summary come from the included method note.", notes["j57"]["claim_ceiling"]),
        _node("uncertainty:encoding", "uncertainty", notes["c61"]["summary"], sources["method_notes"], "CANDIDATE_SOURCE", "Candidate status comes from the included method note.", notes["c61"]["claim_ceiling"]),
    ]

    def edge(edge_id: str, source_id: str, target_id: str, kind: str, source: dict[str, Any]) -> dict[str, Any]:
        return {"id": edge_id, "source": source_id, "target": target_id, "type": kind, "provenance": {"path": source["path"], "sha256": source["sha256"]}, "human_review_status": "HUMAN_CURATED"}

    edges = [
        edge("edge:qwen-support", "evidence:qwen", "claim:verification", "supports", sources["model_results"]),
        edge("edge:haiku-support", "evidence:haiku", "claim:verification", "supports", sources["model_results"]),
        edge("edge:codex-support-objection", "evidence:codex", "objection:capability", "supports", sources["model_results"]),
        edge("edge:objection-attack", "objection:capability", "claim:verification", "attacks", sources["model_results"]),
        edge("edge:rebuttal", "rebuttal:single-output", "objection:capability", "rebuts", sources["model_results"]),
        edge("edge:scope-dependency", "claim:verification", "assumption:transfer", "depends_on", sources["model_results"]),
        edge("edge:j57-support", "evidence:j57", "claim:verification", "supports", sources["method_notes"]),
        edge("edge:encoding-undercut", "uncertainty:encoding", "objection:capability", "undercuts", sources["method_notes"]),
    ]
    return {
        "schema": "aletheia.portable.argument_graph.v1",
        "case_id": "jump-system-independent-verification",
        "title": "When can we trust an AI science idea?",
        "data_author": "human:project-aletheia-portable-extract",
        "runtime_egress": False,
        "top_claim_id": "claim:verification",
        "strongest_objection_id": "objection:capability",
        "contract": {
            "edge_direction": "source_acts_on_target",
            "mandatory_node_ids": ["assumption:transfer", "objection:capability", "rebuttal:single-output", "evidence:j57", "uncertainty:encoding"],
            "candidate_only_node_ids": ["uncertainty:encoding"],
            "forbidden_claim_phrases": ["autonomous scientific discovery", "general scientific discovery", "solves scientific discovery"],
        },
        "nodes": nodes,
        "edges": edges,
    }
