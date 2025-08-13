"""Load compliance rules"""

import re
from dataclasses import dataclass
from typing import List

# Expected file format (pipe-delimited, one per line):
# RULE_ID|SEVERITY|TYPE|VALUE|TIP
# Example:
# CLAIMS_001|high|regex|\b(guarantee|warranty for life)\b|Avoid absolute lifetime claims
# BRAND_001|medium|forbid_words|fake,replica|Remove counterfeit indicators
# SAFETY_001|high|forbid_words|knife,weapon for kids|Remove unsafe terms for kids category

@dataclass
class Rule:
    rule_id: str
    severity: str    # "low" | "medium" | "high" | "critical"
    rtype: str       # "regex" | "forbid_words" | "require_words"
    value: str
    tip: str

SEVERITY_PENALTY = {"low": 5, "medium": 10, "high": 20, "critical": 40}

def load_rules(path: str = "compliance_rules/compliance_rules.txt") -> List[Rule]:
    rules: List[Rule] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split("|")
            if len(parts) < 5:
                continue
            rule_id, severity, rtype, value, tip = parts[:5]
            rules.append(Rule(rule_id=rule_id, severity=severity.lower(), rtype=rtype, value=value, tip=tip))
    return rules

def evaluate_rules(text: str, rules: List[Rule]):
    """
    Returns a list of violations: [{rule_id, severity, tip, evidence}]
    """
    text_low = text.lower()
    findings = []
    for r in rules:
        try:
            if r.rtype == "regex":
                pattern = re.compile(r.value, flags=re.IGNORECASE)
                if pattern.search(text):
                    findings.append({"rule_id": r.rule_id, "severity": r.severity, "tip": r.tip, "evidence": "regex_match"})
            elif r.rtype == "forbid_words":
                # comma-separated words
                words = [w.strip().lower() for w in r.value.split(",") if w.strip()]
                hits = [w for w in words if w in text_low]
                if hits:
                    findings.append({"rule_id": r.rule_id, "severity": r.severity, "tip": r.tip, "evidence": f"forbidden:{','.join(hits)}"})
            elif r.rtype == "require_words":
                words = [w.strip().lower() for w in r.value.split(",") if w.strip()]
                missing = [w for w in words if w not in text_low]
                if missing:
                    findings.append({"rule_id": r.rule_id, "severity": r.severity, "tip": f"Add required terms: {', '.join(missing)}"})
        except Exception:
            # Skip broken rule lines
            continue
    return findings

def score_from_findings(findings):
    score = 100
    deductions = 0
    for f in findings:
        deductions += SEVERITY_PENALTY.get(f["severity"], 10)
    score = max(0, 100 - deductions)
    return score
