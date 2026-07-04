"""
main.py
Entry point: PDF in -> extraction -> standardization -> rule-based
inference -> readable report out.

Usage:
    python main.py path/to/report.pdf
"""

import sys
import json

from extractor import extract_text_and_tables
from standardizer import load_reference_ranges, standardize_report
from rule_engine import load_correlation_rules, run_inference


DISCLAIMER = (
    "DISCLAIMER: This tool provides rule-based pattern flagging for "
    "educational purposes only. It is NOT a medical diagnostic "
    "tool and should never replace professional medical advice."
)


def print_report(standardized_data: dict, inference: dict):
    print("=" * 60)
    print("BLOOD REPORT ANALYSIS")
    print("=" * 60)

    print("\n--- Extracted & Standardized Parameters ---")
    if not standardized_data:
        print("No recognized parameters found. Check PDF format / aliases config.")
    for key, val in standardized_data.items():
        print(f"  {key}: {val['value']} (raw label: '{val['raw_label']}')")

    print("\n--- Abnormalities ---")
    if not inference["abnormalities"]:
        print("  None detected.")
    for a in inference["abnormalities"]:
        print(f"  [{a['status'].upper()}] {a['parameter']}: {a['value']} {a['unit']} "
              f"(expected {a['expected_range']})")

    print("\n--- Possible Correlations ---")
    if not inference["correlations"]:
        print("  None detected.")
    for c in inference["correlations"]:
        print(f"  [{c['flag']}] {c['message']}")

    print("\n" + DISCLAIMER)
    print("=" * 60)


def analyze(pdf_path: str) -> dict:
    reference_ranges = load_reference_ranges()
    correlation_rules = load_correlation_rules()

    extracted = extract_text_and_tables(pdf_path)
    standardized_data = standardize_report(extracted, reference_ranges)
    inference = run_inference(standardized_data, reference_ranges, correlation_rules)

    return {
        "standardized_data": standardized_data,
        "inference": inference
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_pdf>")
        sys.exit(1)

    result = analyze(sys.argv[1])
    print_report(result["standardized_data"], result["inference"])


    with open("last_analysis_output.json", "w") as f:
        json.dump(result, f, indent=2)
