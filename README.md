# Blood Report Analyzer

A rule-based pipeline that reads a blood report PDF, extracts and standardizes
the test values, flags abnormalities against reference ranges, and infers
possible clinical correlations across multiple parameters.

**This is an educational/portfolio project, not a medical diagnostic tool.**

## Pipeline

```
PDF report
   │
   ▼
extractor.py        -> raw text + tables (pdfplumber)
   │
   ▼
standardizer.py      -> maps lab-specific labels (e.g. "SGPT", "Hb", "FBS")
   │                     to standardized parameter keys using an alias config
   ▼
rule_engine.py        -> flags abnormal values vs reference ranges,
   │                      evaluates multi-parameter correlation rules
   ▼
main.py               -> prints a readable report + dumps JSON output
```

## Project structure

```
blood_report_analyzer/
├── main.py                        # orchestrates the full pipeline
├── extractor.py                   # PDF -> raw text/tables
├── standardizer.py                # raw data -> standardized parameters
├── rule_engine.py                 # abnormality + correlation inference
├── config/
│   ├── reference_ranges.json      # normal ranges + label aliases per test
│   └── correlation_rules.json     # multi-parameter correlation rules
└── sample_report.pdf              # sample test report for demo
```

## Running it

```bash
pip install pdfplumber
python main.py sample_report.pdf
```

Output includes:
- Standardized parameters extracted from the report
- Individual abnormalities (high/low vs reference range)
- Possible correlations across parameters (e.g. high glucose + high liver
  enzymes -> possible metabolic/liver correlation)

A `last_analysis_output.json` file is also written with the same data in
machine-readable form.

## How standardization handles messy labels

Different labs name the same test differently (e.g. "SGPT", "ALT",
"Alanine Aminotransferase" are all the same test). `reference_ranges.json`
stores a list of known aliases per parameter, and `standardizer.py` matches
extracted labels against these aliases (case-insensitive, punctuation-stripped,
partial match fallback).

## How correlation rules work

Each rule in `correlation_rules.json` is a small condition string using
`high('param_key')` / `low('param_key')`, evaluated in a restricted namespace
(no builtins) against the standardized data. This keeps rules declarative and
easy to extend without touching the rule engine code — adding a new
correlation is just adding a new JSON entry.

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

This project is intentionally scoped around the document-processing side —
PDF scraping, data extraction, cleaning/standardization, and a declarative
rules engine — rather than around pipeline orchestration. It's a single-
document, on-demand pipeline (like a request handler), not a scheduled batch
job, so something like an Airflow DAG isn't a natural fit here; that kind of
orchestration made more sense for a separate, dedicated data-engineering
project (`aqi-pipeline` — ingestion → warehouse → dbt → Airflow → dashboard)
that now covers that ground. If this project ever needed
to process a folder of reports on a schedule rather than one PDF per run,
that would be the trigger to revisit orchestration — but it isn't there yet.

Remaining gaps worth closing:
- Works reliably on text-based (digitally generated) PDFs. Scanned/image-based
  reports are not yet supported — would need an OCR step (e.g. Tesseract)
  before the standardization stage.
- Alias matching is rule-based; a wider variety of real-world lab report
  formats would help harden the parsing logic.
- Correlation rules currently cover a handful of well-known patterns
  (metabolic/liver, diabetes, lipid/cardiovascular, renal, thyroid/anemia,
  infection). More rules can be added purely via config, no code changes.
- No persistence layer yet (e.g. SQLite) for tracking a patient's reports
  over time.

An ML angle to explore going forward:
- Swap/augment the hand-written alias matching with a trained
  extraction/classification model (e.g. a lightweight NER or table-structure
  model) so parsing generalizes to lab formats that weren't hand-coded.
- Learn correlation/risk patterns from labeled data instead of only
  hand-authored rule conditions, with the rule engine kept as an
  interpretable baseline/fallback.

## Disclaimer

All correlation logic is based on general, publicly known clinical
associations for demonstration purposes. This tool does not use proprietary
medical data and is not intended to diagnose, treat, or provide medical
advice. Always consult a qualified healthcare professional.
