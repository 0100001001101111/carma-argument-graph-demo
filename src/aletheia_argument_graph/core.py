"""Deterministic validation and Dung projection for a bounded argument graph."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


NODE_TYPES = {"claim", "evidence", "assumption", "objection", "rebuttal", "uncertainty"}
EDGE_TYPES = {"supports", "attacks", "undercuts", "rebuts", "depends_on"}
ATTACK_TYPES = {"attacks", "undercuts", "rebuts"}
CONFIDENCE_BY_STATUS = {
    "DIRECT_SOURCE": "SOURCE_MATCH",
    "VERIFIED_SOURCE": "VERIFIED_METHOD",
    "CANDIDATE_SOURCE": "CANDIDATE",
    "HUMAN_SYNTHESIS": "BOUNDED_SYNTHESIS",
    "LLM_PROPOSED": "UNTRUSTED_PROPOSAL",
}
ALLOWED_ENDPOINTS = {
    "supports": ({"evidence", "rebuttal", "claim"}, {"claim", "objection", "rebuttal"}),
    "attacks": ({"claim", "objection", "rebuttal", "uncertainty"}, {"claim", "objection", "rebuttal"}),
    "undercuts": ({"uncertainty", "objection", "rebuttal"}, {"claim", "evidence", "objection", "rebuttal"}),
    "rebuts": ({"rebuttal", "objection", "claim"}, {"claim", "objection", "rebuttal"}),
    "depends_on": ({"claim", "objection", "rebuttal"}, {"assumption", "evidence", "claim"}),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_graph(graph: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    contract = graph.get("contract", {})
    if contract.get("edge_direction") != "source_acts_on_target":
        errors.append("edge_direction_not_frozen")
    if graph.get("data_author", "").startswith("model:") or graph.get("runtime_egress"):
        errors.append("llm_or_egress_in_verdict_path")

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = node.get("id")
        if not node_id or node_id in by_id:
            errors.append(f"duplicate_or_missing_node_id:{node_id}")
            continue
        by_id[node_id] = node
        if node.get("type") not in NODE_TYPES:
            errors.append(f"invalid_node_type:{node_id}")
        source = node.get("source", {})
        path = Path(source.get("path", ""))
        if not path.is_file():
            errors.append(f"missing_source:{node_id}")
        elif _sha256(path) != source.get("sha256"):
            errors.append(f"source_hash_mismatch:{node_id}")
        if not node.get("claim_ceiling"):
            errors.append(f"missing_claim_ceiling:{node_id}")
        status = node.get("validation_status")
        confidence = node.get("confidence", {})
        expected_level = CONFIDENCE_BY_STATUS.get(status)
        if expected_level is None or confidence.get("level") != expected_level or not confidence.get("basis"):
            errors.append(f"confidence_policy_mismatch:{node_id}")
        if status == "LLM_PROPOSED" and node.get("type") == "evidence":
            errors.append(f"unsupported_promotion:{node_id}")

    edge_ids: set[str] = set()
    for edge in edges:
        edge_id = edge.get("id")
        if not edge_id or edge_id in edge_ids:
            errors.append(f"duplicate_or_missing_edge_id:{edge_id}")
            continue
        edge_ids.add(edge_id)
        source_id, target_id, kind = edge.get("source"), edge.get("target"), edge.get("type")
        if source_id not in by_id or target_id not in by_id:
            errors.append(f"dangling_edge:{edge_id}")
            continue
        if kind not in EDGE_TYPES:
            errors.append(f"invalid_edge_type:{edge_id}")
            continue
        allowed_source, allowed_target = ALLOWED_ENDPOINTS[kind]
        if by_id[source_id]["type"] not in allowed_source or by_id[target_id]["type"] not in allowed_target:
            errors.append(f"invalid_edge_endpoints:{edge_id}")
        path = Path(edge.get("provenance", {}).get("path", ""))
        if not path.is_file():
            errors.append(f"missing_edge_provenance:{edge_id}")
        elif _sha256(path) != edge.get("provenance", {}).get("sha256"):
            errors.append(f"edge_provenance_hash_mismatch:{edge_id}")

    mandatory_ids = set(contract.get("mandatory_node_ids", []))
    for required_id in sorted(mandatory_ids):
        if required_id not in by_id:
            errors.append(f"missing_mandatory_node:{required_id}")
    candidate_ids = set(contract.get("candidate_only_node_ids", []))
    for edge in edges:
        if edge.get("source") in candidate_ids and edge.get("type") not in {"undercuts", "depends_on"}:
            errors.append(f"candidate_overpromoted:{edge.get('id')}")

    top_claim_id = graph.get("top_claim_id")
    objection_id = graph.get("strongest_objection_id")
    if objection_id not in by_id or by_id.get(objection_id, {}).get("type") != "objection":
        errors.append("missing_selected_objection")
    elif not any(e.get("source") == objection_id and e.get("target") == top_claim_id and e.get("type") in ATTACK_TYPES for e in edges):
        errors.append("selected_objection_not_connected")
    if top_claim_id not in by_id or by_id.get(top_claim_id, {}).get("type") != "claim":
        errors.append("missing_top_claim")
    else:
        text = by_id[top_claim_id].get("text", "").lower()
        if any(phrase.lower() in text for phrase in contract.get("forbidden_claim_phrases", [])):
            errors.append("claim_exceeds_ceiling")
        direct_support = [e for e in edges if e.get("type") == "supports" and e.get("target") == top_claim_id and by_id.get(e.get("source"), {}).get("type") == "evidence"]
        if not direct_support:
            errors.append("top_claim_has_no_direct_evidence")

    dependency_map = {node_id: set() for node_id in by_id}
    for edge in edges:
        if edge.get("type") == "depends_on" and edge.get("source") in by_id and edge.get("target") in by_id:
            dependency_map[edge["source"]].add(edge["target"])
    visiting: set[str] = set()
    visited: set[str] = set()

    def has_cycle(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        if any(has_cycle(target_id) for target_id in dependency_map[node_id]):
            return True
        visiting.remove(node_id)
        visited.add(node_id)
        return False

    if any(has_cycle(node_id) for node_id in sorted(by_id) if node_id not in visited):
        errors.append("depends_on_cycle")
    return {"state": "ACCEPT" if not errors else "REJECT", "errors": sorted(set(errors))}


def grounded_semantics(graph: dict[str, Any]) -> dict[str, list[str]]:
    """Compute grounded labels for the frozen node-attack projection."""
    arguments = {node["id"] for node in graph["nodes"]}
    attacks = {(edge["source"], edge["target"]) for edge in graph["edges"] if edge["type"] in ATTACK_TYPES}
    attackers = {arg: {source for source, target in attacks if target == arg} for arg in arguments}
    accepted: set[str] = set()
    rejected: set[str] = set()
    changed = True
    while changed:
        changed = False
        for argument in sorted(arguments - accepted - rejected):
            if attackers[argument] <= rejected:
                accepted.add(argument)
                changed = True
        newly_rejected = {target for source, target in attacks if source in accepted and target not in accepted}
        if not newly_rejected <= rejected:
            rejected |= newly_rejected
            changed = True
    undecided = arguments - accepted - rejected
    supported_accepted = []
    for node in graph["nodes"]:
        if node["type"] != "claim" or node["id"] not in accepted:
            continue
        if any(edge["type"] == "supports" and edge["target"] == node["id"] and edge["source"] in accepted for edge in graph["edges"]):
            supported_accepted.append(node["id"])
    return {
        "dialectically_accepted": sorted(accepted),
        "dialectically_rejected": sorted(rejected),
        "dialectically_undecided": sorted(undecided),
        "accepted_with_direct_support": sorted(supported_accepted),
    }
