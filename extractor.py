"""
extractor.py
Reads a PDF blood report and returns raw text + any extracted tables.
Uses pdfplumber, which works well for text-based (non-scanned) PDFs.
"""

import pdfplumber


def extract_text_and_tables(pdf_path: str):
    """
    Extract raw text and tables from all pages of a PDF.

    Returns:
        dict with:
            'text': full concatenated text (str)
            'tables': list of tables, each table is a list of rows (list of lists)
    """
    full_text = []
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text)

            tables = page.extract_tables()
            for table in tables:
                if table:
                    all_tables.append(table)

    return {
        "text": "\n".join(full_text),
        "tables": all_tables
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <path_to_pdf>")
        sys.exit(1)

    result = extract_text_and_tables(sys.argv[1])
    print("--- Extracted Text ---")
    print(result["text"][:1000])
    print("\n--- Tables Found ---")
    print(f"{len(result['tables'])} table(s) detected")
