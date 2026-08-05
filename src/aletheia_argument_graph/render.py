"""Render the verified case as one phone-readable HTML page."""
from __future__ import annotations

from html import escape
from typing import Any


def render_html(graph: dict[str, Any], semantics: dict[str, list[str]]) -> str:
    nodes = {node["id"]: node for node in graph["nodes"]}
    qwen = escape(nodes["evidence:qwen"]["text"].split(" in ", 1)[1].split(" frozen", 1)[0])
    haiku = escape(nodes["evidence:haiku"]["text"].split(" in ", 1)[1].split(" frozen", 1)[0])
    codex = escape(nodes["evidence:codex"]["text"].split(" in ", 1)[1].split(" frozen", 1)[0])
    supported = graph["top_claim_id"] in semantics["accepted_with_direct_support"]
    result = "AI can produce a useful idea." if supported else "The claim did not clear the full gate."
    conclusion = escape(nodes[graph["top_claim_id"]]["text"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(graph['title'])}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0d121a;color:#f4f7fb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{width:min(1200px,100%);margin:auto;padding:6vw}}.eyebrow{{color:#72c9ff;font-size:20px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}}h1{{font-size:clamp(44px,6vw,72px);line-height:1.03;margin:18px 0 24px}}.lead{{color:#c7d0dc;font-size:clamp(20px,2.4vw,30px);line-height:1.35;margin-bottom:44px}}.step{{background:#182231;border:2px solid #2b3a4e;border-radius:28px;padding:32px}}.title{{font-size:30px;font-weight:850;margin-bottom:22px}}.num{{display:inline-grid;place-items:center;width:46px;height:46px;border-radius:50%;background:#72c9ff;color:#071019;margin-right:12px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}.box{{padding:24px;border-radius:20px;background:#101722;border:2px solid #34475f;font-size:23px}}.box b{{display:block;font-size:26px;margin-bottom:8px}}.score{{font-size:36px;font-weight:900}}.zero{{color:#ff7b85}}.mixed{{color:#ffd166}}.check strong{{display:block;color:#79e2a7;font-size:34px}}.arrow{{text-align:center;color:#72c9ff;font-size:58px;padding:18px}}.result{{border-color:#42cc83;background:#122b25}}.result h2{{font-size:42px;margin:0 0 15px}}.result p{{font-size:25px;line-height:1.4}}footer{{margin-top:38px;color:#9cacbf;text-align:center;font-size:20px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}main{{padding:28px 18px}}}}
</style></head><body><main><div class="eyebrow">Project Aletheia · argument graph work sample</div><h1>{escape(graph['title'])}</h1><p class="lead">An AI answer can sound convincing and still be wrong. This system makes the idea show its evidence and face a selected strong objection.</p>
<section class="step"><div class="title"><span class="num">1</span>The AI tries the sealed challenge</div><div class="grid"><div class="box"><b>Qwen</b><span class="score zero">{qwen}</span></div><div class="box"><b>Haiku</b><span class="score zero">{haiku}</span></div><div class="box"><b>Codex</b><span class="score mixed">{codex}</span></div></div></section><div class="arrow">↓</div>
<section class="step"><div class="title"><span class="num">2</span>The verifier checks the argument</div><div class="grid"><div class="box check"><strong>✓</strong>Do the numbers come from the included evidence?</div><div class="box check"><strong>✓</strong>Is the selected objection present and connected?</div><div class="box check"><strong>✓</strong>Can pure Python reproduce the result?</div></div></section><div class="arrow">↓</div>
<section class="step result"><div class="title"><span class="num">3</span>What survives</div><h2>{escape(result)}</h2><p>{conclusion}</p></section><footer>One guided-rediscovery task · deterministic verifier · no LLM in the verdict path</footer></main></body></html>"""
