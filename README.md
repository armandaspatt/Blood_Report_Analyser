#  Blood Report Analyzer

A rule-based pipeline that reads a blood test report PDF, extracts and standardizes the values, flags abnormalities against reference ranges, and infers possible clinical correlations across multiple parameters — with a Streamlit web UI on top.

**Live demo:** [armandaspatt-blood-report-analyser-app-llmfpr.streamlit.app](https://armandaspatt-blood-report-analyser-app-llmfpr.streamlit.app/)
Use `sample_report.pdf` from this repo to try it out quickly.

> ⚠️ **This is an educational/portfolio project, not a medical diagnostic tool.** Correlation logic is based on general, publicly known clinical associations. Always consult a qualified healthcare professional.

---

## Screenshots

**Upload & analyze a report**
![App home screen](screenshots/app_home.png)

**Extracted parameters & flagged abnormalities**
![Extracted parameters and abnormalities](screenshots/extracted_parameters.png)

**Possible cross-parameter correlations**
![Possible correlations](screenshots/possible_correlations.png)

---

## How it works

```
PDF report
   │
   ▼
extractor.py         -> raw text + tables (pdfplumber)
   │
   ▼
standardizer.py       -> maps lab-specific labels (e.g. "SGPT", "Hb", "FBS")
   │                     to standardized parameter keys using an alias config
   ▼
rule_engine.py         -> flags abnormal values vs reference ranges,
   │                      evaluates multi-parameter correlation rules
   ▼
main.py / app.py        -> CLI report or Streamlit UI + JSON output
```

## Features

- **PDF extraction** – pulls raw text and tables out of digitally generated blood report PDFs
- **Label standardization** – normalizes messy, lab-specific naming (e.g. "SGPT" → ALT) via a configurable alias list
- **Abnormality detection** – compares every extracted value against reference ranges and flags HIGH/LOW
- **Cross-parameter correlations** – applies declarative rules (config-driven, no code changes needed) to surface patterns like a possible metabolic/liver link, a diabetes pattern, or a thyroid–anemia link
- **Two interfaces** – a CLI (`main.py`) for scripting and a Streamlit web app (`app.py`) for interactive use
- **JSON output** – every run also writes a machine-readable `last_analysis_output.json`

## Project structure

```
Blood_Report_Analyser/
├── app.py                         # Streamlit web app
├── main.py                        # CLI entry point / orchestrates the pipeline
├── extractor.py                   # PDF -> raw text/tables
├── standardizer.py                # raw data -> standardized parameters
├── rule_engine.py                 # abnormality + correlation inference
├── config/
│   ├── reference_ranges.json      # normal ranges + label aliases per test
│   └── correlation_rules.json     # multi-parameter correlation rules
├── sample_report.pdf              # sample test report for demo
└── requirements.txt
```

Output includes:
- Standardized parameters extracted from the report
- Individual abnormalities (high/low vs reference range)
- Possible correlations across parameters (e.g. high glucose + high liver enzymes → possible metabolic/liver correlation)

A `last_analysis_output.json` file is also written with the same data in machine-readable form.

## How standardization handles messy labels

Different labs name the same test differently (e.g. "SGPT", "ALT", "Alanine Aminotransferase" are all the same test). `reference_ranges.json` stores a list of known aliases per parameter, and `standardizer.py` matches extracted labels against these aliases (case-insensitive, punctuation-stripped, with a partial-match fallback).

## How correlation rules work

Each rule in `correlation_rules.json` is a small condition string using `high('param_key')` / `low('param_key')`, evaluated in a restricted namespace (no builtins) against the standardized data. This keeps rules declarative and easy to extend without touching the rule engine code — adding a new correlation is just adding a new JSON entry.

Example:
```json
{
  "id": "diabetes_liver_pattern",
  "condition": "high('glucose_fasting') and (high('alt') or high('ast'))",
  "message": "Elevated fasting glucose together with elevated liver enzymes...",
  "flag": "possible_metabolic_liver_correlation"
}
```

## Current limitations / next steps

- Works reliably on text-based (digitally generated) PDFs. Scanned/image-based reports aren't yet supported — would need an OCR step (e.g. Tesseract) before the standardization stage.
- Alias matching is rule-based; testing against a wider variety of real-world lab report formats would help harden the parsing logic.
- Correlation rules currently cover a handful of well-known patterns (metabolic/liver, diabetes, lipid/cardiovascular, renal, thyroid/anemia, infection). More rules can be added purely via config, no code changes.
- No persistence layer yet (e.g. SQLite) for tracking a patient's reports over time.

## Disclaimer

All correlation logic is based on general, publicly known clinical associations for demonstration purposes. This tool does not use proprietary medical data and is not intended to diagnose, treat, or provide medical advice. Always consult a qualified healthcare professional.
