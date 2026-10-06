"""
Automated tests for the triage logic (run by pytest in CI).
These test the rule-based method and helpers - no AI model needed, so they
run fast in the CI pipeline.
"""
from triage_lib import rule_triage, _match, CATEGORIES, PRIORITIES


def test_bug_critical():
    cat, pri = rule_triage("Checkout broken", "customers are losing sales every minute")
    assert cat == "Bug"
    assert pri == "Critical"


def test_billing_high():
    cat, pri = rule_triage("Double charged", "I was charged twice for my subscription, please refund")
    assert cat == "Billing"
    assert pri == "High"


def test_feature_request():
    cat, _ = rule_triage("Add dark mode", "would be great if you could add a dark mode")
    assert cat == "Feature Request"


def test_output_labels_are_valid():
    cat, pri = rule_triage("random subject", "random body text")
    assert pri in PRIORITIES


def test_match_picks_option():
    assert _match("this is clearly a Bug", CATEGORIES) == "Bug"


def test_match_falls_back_safely():
    assert _match("gibberish with no label", PRIORITIES) == PRIORITIES[-1]
