"""
app.py
Streamlit frontend for the Blood Report Analyzer pipeline.
Upload a PDF -> see standardized parameters, abnormalities, and
possible correlations rendered as a clean report.
"""

import streamlit as st
import pandas as pd
import tempfile
import os

from extractor import extract_text_and_tables
from standardizer import load_reference_ranges, standardize_report
from rule_engine import load_correlation_rules, run_inference


st.set_page_config(
    page_title="Blood Report Analyzer",
    page_icon="🩸",
    layout="centered"
)

# ---- minimal custom styling ----
st.markdown("""
<style>
    .main .block-container { padding-top: 2.5rem; max-width: 780px; }
    .status-high { color: #c0392b; font-weight: 600; }
    .status-low { color: #d68910; font-weight: 600; }
    .correlation-card {
        background-color: #f5f7fa;
        border-left: 4px solid #4a7bab;
        padding: 0.9rem 1.1rem;
        border-radius: 6px;
        margin-bottom: 0.7rem;
    }
    .disclaimer-box {
        background-color: #fff8e1;
        border-left: 4px solid #e6b800;
        padding: 0.8rem 1.1rem;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #6b5900;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🩸 Blood Report Analyzer")
st.caption("Upload a blood test report (PDF) to extract, standardize, and analyze results.")

uploaded_file = st.file_uploader("Upload a blood report PDF", type=["pdf"])

st.markdown("""
<div class="disclaimer-box">
⚠️ <strong>Disclaimer:</strong> This is a rule-based educational/portfolio project,
not a medical diagnostic tool. Correlation logic is based on general, publicly known
clinical associations. Always consult a qualified healthcare professional.
</div>
""", unsafe_allow_html=True)

if uploaded_file is not None:
    with st.spinner("Extracting and analyzing report..."):
        # write uploaded file to a temp path so pdfplumber can read it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            reference_ranges = load_reference_ranges()
            correlation_rules = load_correlation_rules()

            extracted = extract_text_and_tables(tmp_path)
            standardized_data = standardize_report(extracted, reference_ranges)
            inference = run_inference(standardized_data, reference_ranges, correlation_rules)
        finally:
            os.unlink(tmp_path)

    if not standardized_data:
        st.warning(
            "No recognized parameters found. This works best on text-based "
            "(non-scanned) PDF lab reports with standard test names."
        )
    else:
        st.success(f"Found {len(standardized_data)} recognized parameter(s).")

        # ---- Standardized parameters table ----
        st.subheader("Extracted Parameters")
        rows = []
        abnormal_lookup = {a["parameter"]: a["status"] for a in inference["abnormalities"]}
        for key, val in standardized_data.items():
            ref = reference_ranges.get(key, {})
            status = abnormal_lookup.get(key, "normal")
            rows.append({
                "Parameter": key.replace("_", " ").title(),
                "Value": val["value"],
                "Unit": ref.get("unit", ""),
                "Reference Range": f"{ref.get('low', '?')}-{ref.get('high', '?')}" if ref else "—",
                "Status": status.upper()
            })
        df = pd.DataFrame(rows)

        def highlight_status(row):
            color = ""
            if row["Status"] == "HIGH":
                color = "background-color: #fdecea"
            elif row["Status"] == "LOW":
                color = "background-color: #fef5e7"
            return [color] * len(row)

        st.dataframe(
            df.style.apply(highlight_status, axis=1),
            use_container_width=True,
            hide_index=True
        )

        # ---- Abnormalities summary ----
        st.subheader("Abnormalities")
        if not inference["abnormalities"]:
            st.info("No abnormal values detected.")
        else:
            for a in inference["abnormalities"]:
                css_class = "status-high" if a["status"] == "high" else "status-low"
                st.markdown(
                    f"- **{a['parameter'].replace('_', ' ').title()}**: "
                    f"<span class='{css_class}'>{a['value']} {a['unit']} "
                    f"({a['status'].upper()})</span> — expected {a['expected_range']}",
                    unsafe_allow_html=True
                )

        # ---- Correlations ----
        st.subheader("Possible Correlations")
        if not inference["correlations"]:
            st.info("No multi-parameter correlations detected.")
        else:
            for c in inference["correlations"]:
                st.markdown(f"""
                <div class="correlation-card">
                    <strong>{c['flag'].replace('_', ' ').title()}</strong><br>
                    {c['message']}
                </div>
                """, unsafe_allow_html=True)

        # ---- Raw JSON (expandable, for technical reviewers) ----
        with st.expander("View raw output (JSON)"):
            st.json({
                "standardized_data": standardized_data,
                "inference": inference
            })
else:
    st.info("👆 Upload a PDF blood report to get started, or try the sample report in the repo (`sample_report.pdf`).")
