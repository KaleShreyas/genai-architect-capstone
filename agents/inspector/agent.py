"""Rule checks and scoring"""

import json
import os
from typing import Dict, Any, List

from langfuse import Langfuse

from agents.inspector.rules_loader import load_rules, evaluate_rules, score_from_findings
from agents.inspector.taxonomy import align_category
from db.crud import update_status, update_inspector_verdict

APPROVE_THRESHOLD = int(os.getenv("APPROVE_THRESHOLD", "80"))
NEEDS_FIX_THRESHOLD = int(os.getenv("NEEDS_FIX_THRESHOLD", "50"))

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def _collect_text_fields(state: Dict[str, Any]) -> str:
    parts = []
    for k in ("title", "seo_title", "description", "seo_description", "brand", "category"):
        v = state.get(k)
        if v:
            parts.append(f"{k}: {v}")
    # include attributes
    attrs = state.get("attributes") or {}
    if isinstance(attrs, dict) and attrs:
        parts.append(f"attributes: " + json.dumps(attrs, ensure_ascii=False))
    return "\n".join(parts)

def _decide_status(score: int) -> str:
    if score >= APPROVE_THRESHOLD:
        return "approved"
    if score >= NEEDS_FIX_THRESHOLD:
        return "needs_fix"
    return "rejected"

def run_inspector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node.
    Requires prior Crafter outputs in state:
      - seo_title, seo_description, attributes, hero_image_url, category
    Produces:
      - compliance_score (0-100)
      - issues: list of {rule_id, severity, tip, evidence}
      - aligned_category + score
      - status -> updates DB
    """
    sku = state.get("sku") or state.get("listing_id") or "unknown"
    trace = langfuse.trace(name=f"inspector-{sku}", tags=["inspector", "compliance"], input=state)

    # 1) Load rules
    span_rules = trace.span(name="load-rules")
    rules = load_rules()
    span_rules.end(status="success", output={"rules_count": len(rules)})

    # 2) Evaluate rules on concatenated text
    span_eval = trace.span(name="evaluate-rules")
    text = _collect_text_fields(state)
    findings = evaluate_rules(text, rules)
    base_score = score_from_findings(findings)
    span_eval.end(status="success", output={"findings": findings, "base_score": base_score})

    # 3) Category alignment via Azure Search / Weaviate
    span_tax = trace.span(name="taxonomy-alignment")
    candidate_category = state.get("category") or (state.get("attributes") or {}).get("category")
    aligned_path, align_score, backend = align_category(candidate_category or "")
    # Turn Azure/Weaviate score (0..1-ish) into small bonus/penalty
    alignment_bonus = 0
    if align_score >= 0.75:
        alignment_bonus = 5
    elif align_score <= 0.2 and candidate_category:
        alignment_bonus = -10
        findings.append({
            "rule_id": "TAXONOMY_MISMATCH",
            "severity": "medium",
            "tip": f"Category may be incorrect. Suggested: {aligned_path or 'N/A'}",
            "evidence": f"align_score={align_score:.2f} backend={backend}"
        })
    span_tax.end(status="success", output={"aligned_path": aligned_path, "align_score": align_score, "backend": backend})

    # 4) Final score & decision
    final_score = max(0, min(100, base_score + alignment_bonus))
    status = _decide_status(final_score)

    verdict = {
        "sku": sku,
        "final_score": final_score,
        "status": status,
        "issues": findings,
        "aligned_category": aligned_path,
        "alignment_score": align_score,
        "alignment_backend": backend
    }

    # 5) Update DB
    update_inspector_verdict(
        sku=sku,
        score=final_score,
        issues_json=json.dumps(findings, ensure_ascii=False),
        aligned_category=aligned_path
    )
    update_status(sku, status)

    trace.end(status="success", output=verdict)

    # 6) Emit structured result for orchestrator
    return {
        **state,
        "compliance_score": final_score,
        "issues": findings,
        "aligned_category": aligned_path,
        "status": status,
        "inspector_done": True
    }
