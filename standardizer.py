"""
standardizer.py
Takes raw extracted text/tables and standardizes them into a clean
structured format: {parameter_key: {"value": float, "unit": str, "raw_label": str}}

Handles the fact that different labs name/format the same test differently
(e.g. "Hb", "Hemoglobin", "HGB" all mean the same thing).
"""

import re
import json


def load_reference_ranges(config_path: str = "config/reference_ranges.json") -> dict:
    with open(config_path, "r") as f:
        return json.load(f)


def build_alias_lookup(reference_ranges: dict) -> dict:
    """
    Builds a flat lookup: alias_string -> standardized_parameter_key
    """
    lookup = {}
    for param_key, meta in reference_ranges.items():
        for alias in meta["aliases"]:
            lookup[alias.lower().strip()] = param_key
    return lookup


# Matches lines like: "Hemoglobin   13.5   g/dL   12.0-16.5"
# or table rows already split into cells.
VALUE_PATTERN = re.compile(r"([-+]?\d*\.?\d+)")


def _try_match_alias(label: str, alias_lookup: dict):
    label_clean = re.sub(r"[^a-z0-9 ]", "", label.lower()).strip()
    if label_clean in alias_lookup:
        return alias_lookup[label_clean]
    # fallback: partial containment match (handles extra words like "Serum Creatinine Level")
    for alias, key in alias_lookup.items():
        if alias in label_clean:
            return key
    return None


def standardize_from_lines(lines, alias_lookup: dict) -> dict:
    """
    Parses a list of text lines (e.g. split from raw extracted text)
    and returns standardized parameter values.
    """
    standardized = {}

    for line in lines:
        if not line.strip():
            continue

        # split label from the rest by finding first numeric token
        match = VALUE_PATTERN.search(line)
        if not match:
            continue

        label_part = line[:match.start()].strip(" :\t-")
        value_str = match.group(1)

        param_key = _try_match_alias(label_part, alias_lookup)
        if not param_key:
            continue

        try:
            value = float(value_str)
        except ValueError:
            continue

        standardized[param_key] = {
            "value": value,
            "raw_label": label_part
        }

    return standardized


def standardize_from_tables(tables, alias_lookup: dict) -> dict:
    """
    Parses table rows (list of lists) into standardized parameter values.
    Assumes typical layout: [test_name, value, unit, reference_range] in some order.
    """
    standardized = {}

    for table in tables:
        for row in table:
            if not row or len(row) < 2:
                continue

            row_cells = [str(c) if c is not None else "" for c in row]
            label_cell = row_cells[0]

            param_key = _try_match_alias(label_cell, alias_lookup)
            if not param_key:
                continue

            # find first numeric-looking cell after the label
            value = None
            for cell in row_cells[1:]:
                m = VALUE_PATTERN.search(cell)
                if m:
                    try:
                        value = float(m.group(1))
                        break
                    except ValueError:
                        continue

            if value is not None:
                standardized[param_key] = {
                    "value": value,
                    "raw_label": label_cell
                }

    return standardized


def standardize_report(extracted: dict, reference_ranges: dict) -> dict:
    """
    Main entry point: takes extractor.py output and returns standardized data.
    Table-based extraction takes priority (more reliable); falls back to
    line-based text parsing for anything not found in tables.
    """
    alias_lookup = build_alias_lookup(reference_ranges)

    from_tables = standardize_from_tables(extracted.get("tables", []), alias_lookup)

    lines = extracted.get("text", "").split("\n")
    from_text = standardize_from_lines(lines, alias_lookup)

    # merge: table data wins if there's a conflict
    merged = {**from_text, **from_tables}
    return merged


if __name__ == "__main__":
    import sys
    from extractor import extract_text_and_tables

    if len(sys.argv) < 2:
        print("Usage: python standardizer.py <path_to_pdf>")
        sys.exit(1)

    ref_ranges = load_reference_ranges()
    extracted = extract_text_and_tables(sys.argv[1])
    result = standardize_report(extracted, ref_ranges)

    print("--- Standardized Parameters ---")
    for key, val in result.items():
        print(f"{key}: {val['value']} (from '{val['raw_label']}')")
