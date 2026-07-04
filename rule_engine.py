"""
rule_engine.py
Two jobs:
1. Flag individual abnormal values against reference ranges.
2. Evaluate multi-parameter correlation rules (loaded from config) to
   surface possible clinical patterns.

NOTE: This is a rule-based educational/portfolio project, not a diagnostic
tool. Correlation messages are deliberately phrased as "possible" /
"can co-occur with" rather than definitive diagnoses, and are based on
well-established, publicly known clinical associations (not proprietary
medical data).
"""

import json


def load_correlation_rules(config_path: str = "config/correlation_rules.json") -> list:
    with open(config_path, "r") as f:
        return json.load(f)


def flag_abnormalities(standardized_data: dict, reference_ranges: dict) -> list:
    """
    Compares each standardized value against its reference range.
    Returns a list of abnormality dicts.
    """
    abnormalities = []

    for param_key, data in standardized_data.items():
        ref = reference_ranges.get(param_key)
        if not ref:
            continue

        value = data["value"]
        status = None
        if value < ref["low"]:
            status = "low"
        elif value > ref["high"]:
            status = "high"

        if status:
            abnormalities.append({
                "parameter": param_key,
                "value": value,
                "unit": ref["unit"],
                "expected_range": f"{ref['low']}-{ref['high']} {ref['unit']}",
                "status": status
            })

    return abnormalities


class _ConditionEvaluator:
    """
    Small helper exposing high(param) / low(param) as callables so
    correlation rule conditions (plain strings from config) can be
    evaluated safely without a full custom parser.
    """

    def __init__(self, standardized_data, reference_ranges):
        self.data = standardized_data
        self.ranges = reference_ranges

    def high(self, param_key):
        if param_key not in self.data or param_key not in self.ranges:
            return False
        return self.data[param_key]["value"] > self.ranges[param_key]["high"]

    def low(self, param_key):
        if param_key not in self.data or param_key not in self.ranges:
            return False
        return self.data[param_key]["value"] < self.ranges[param_key]["low"]


def evaluate_correlations(standardized_data: dict, reference_ranges: dict, rules: list) -> list:
    """
    Evaluates each correlation rule's condition string against the data.
    Condition strings look like: "high(glucose_fasting) and high(hba1c)"
    """
    evaluator = _ConditionEvaluator(standardized_data, reference_ranges)
    triggered = []

    # restricted namespace: only 'high' and 'low' are callable, nothing else
    safe_globals = {"__builtins__": {}}
    safe_locals = {"high": evaluator.high, "low": evaluator.low}

    for rule in rules:
        try:
            result = eval(rule["condition"], safe_globals, safe_locals)
        except Exception:
            result = False

        if result:
            triggered.append({
                "rule_id": rule["id"],
                "flag": rule["flag"],
                "message": rule["message"]
            })

    return triggered


def run_inference(standardized_data: dict, reference_ranges: dict, correlation_rules: list) -> dict:
    """
    Full inference pipeline: abnormalities + correlations.
    """
    return {
        "abnormalities": flag_abnormalities(standardized_data, reference_ranges),
        "correlations": evaluate_correlations(standardized_data, reference_ranges, correlation_rules)
    }
