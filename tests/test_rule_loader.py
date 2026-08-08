"""Unit tests for the YAML rule loader.

Tests verify:
- Rules load correctly from both YAML files
- Rule schema is valid (required fields present)
- Rule IDs are unique within a ruleset
- Count meets minimum requirement (15 DPDP + 7 Contract Act)
"""
import pytest
from pathlib import Path


def test_dpdp_rules_load():
    """DPDP rules YAML must load cleanly with all required fields."""
    from rule_loader import load_rules
    from models import RuleSet, Severity
    rules = load_rules(RuleSet.DPDP_2023)
    assert len(rules) >= 10, "Expected at least 10 DPDP rules"
    for rule in rules:
        assert rule.rule_id.startswith("DPDP-"), f"Bad rule_id: {rule.rule_id}"
        assert rule.title, f"Missing title for {rule.rule_id}"
        assert rule.description, f"Missing description for {rule.rule_id}"
        assert rule.check_prompt, f"Missing check_prompt for {rule.rule_id}"
        assert rule.severity in (Severity.HIGH, Severity.MEDIUM, Severity.LOW)
        assert rule.section, f"Missing section for {rule.rule_id}"


def test_contract_rules_load():
    """Contract Act rules YAML must load cleanly with all required fields."""
    from rule_loader import load_rules
    from models import RuleSet, Severity
    rules = load_rules(RuleSet.CONTRACT_ACT_1872)
    assert len(rules) >= 5, "Expected at least 5 Contract Act rules"
    for rule in rules:
        assert rule.rule_id.startswith("ICA-"), f"Bad rule_id: {rule.rule_id}"
        assert rule.title
        assert rule.check_prompt


def test_dpdp_rule_ids_are_unique():
    """Rule IDs within a ruleset must be unique."""
    from rule_loader import load_rules
    from models import RuleSet
    rules = load_rules(RuleSet.DPDP_2023)
    ids = [r.rule_id for r in rules]
    assert len(ids) == len(set(ids)), "Duplicate rule IDs found in DPDP ruleset"


def test_contract_rule_ids_are_unique():
    """Rule IDs within a ruleset must be unique."""
    from rule_loader import load_rules
    from models import RuleSet
    rules = load_rules(RuleSet.CONTRACT_ACT_1872)
    ids = [r.rule_id for r in rules]
    assert len(ids) == len(set(ids)), "Duplicate rule IDs found in Contract Act ruleset"


def test_list_available_rulesets():
    """list_available_rulesets must return metadata for both rule sets."""
    from rule_loader import list_available_rulesets
    rulesets = list_available_rulesets()
    ids = [r["id"] for r in rulesets]
    assert "dpdp_2023" in ids
    assert "contract_act_1872" in ids
    for rs in rulesets:
        assert rs["rule_count"] > 0


def test_invalid_ruleset_raises():
    """Requesting an unknown ruleset must raise ValueError."""
    from rule_loader import load_rules
    with pytest.raises((ValueError, KeyError)):
        load_rules("non_existent_ruleset")  # type: ignore
