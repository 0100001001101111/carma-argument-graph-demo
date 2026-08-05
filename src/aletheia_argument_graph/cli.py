"""Command-line entry point."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .case import build_case_graph
from .core import grounded_semantics, validate_graph
from .render import render_html


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and verify the Aletheia argument graph demo")
    parser.add_argument("--output", default="build", help="output directory relative to the repository")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    output = (root / args.output).resolve()
    graph = build_case_graph(root)
    verdict = validate_graph(graph)
    if verdict["state"] != "ACCEPT":
        raise SystemExit(canonical_json(verdict))
    semantics = grounded_semantics(graph)
    output.mkdir(parents=True, exist_ok=True)
    (output / "argument_graph.json").write_text(canonical_json(graph), encoding="utf-8")
    (output / "semantics.json").write_text(canonical_json({"verdict": verdict, "grounded_semantics": semantics}), encoding="utf-8")
    (output / "index.html").write_text(render_html(graph, semantics), encoding="utf-8")
    print(canonical_json({"verdict": verdict, "grounded_semantics": semantics}), end="")
    return 0
