"""Load and validate YAML rule library files."""
from __future__ import annotations

from pathlib import Path

import yaml

from config import settings
from models import Rule, Severity, RuleSet


_RULESET_FILES: dict[RuleSet, str] = {
    RuleSet.DPDP_2023: "dpdp_2023.yaml",
    RuleSet.CONTRACT_ACT_1872: "contract_act_1872.yaml",
}


def load_rules(ruleset: RuleSet) -> list[Rule]:
    """Load and validate rules from the YAML rule library."""
    rules_dir = Path(settings.rules_dir)
    filename = _RULESET_FILES.get(ruleset)
    if not filename:
        raise ValueError(f"Unknown ruleset: {ruleset}")

    rule_file = rules_dir / filename
    if not rule_file.exists():
        raise FileNotFoundError(f"Rule file not found: {rule_file}")

    with open(rule_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    act = data.get("act", "")
    act_short = data.get("act_short", "")
    raw_rules = data.get("rules", [])

    rules: list[Rule] = []
    for r in raw_rules:
        rules.append(
            Rule(
                rule_id=r["id"],
                act=act,
                act_short=act_short,
                title=r["title"],
                description=r["description"].strip(),
                check_prompt=r["check_prompt"].strip(),
                severity=Severity(r.get("severity", "MEDIUM")),
                section=r.get("section", ""),
            )
        )

    return rules


def list_available_rulesets() -> list[dict]:
    """Return metadata for all available rulesets."""
    result = []
    for ruleset, filename in _RULESET_FILES.items():
        rule_file = Path(settings.rules_dir) / filename
        if rule_file.exists():
            with open(rule_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            result.append({
                "id": ruleset.value,
                "act": data.get("act", ""),
                "act_short": data.get("act_short", ""),
                "rule_count": len(data.get("rules", [])),
            })
    return result
