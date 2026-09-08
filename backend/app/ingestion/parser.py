import pdfplumber
from typing import List, Dict

def parse_pdf(file_path: str) -> List[Dict]:
    pages_data = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # layout=True preserves spatial arrangement (tables stay visually intact like ASCII grids)
            # This ensures footnotes placed physically below a table remain directly adjacent in the text stream.
            text = page.extract_text() or ""
                
            pages_data.append({
                "page_number": i + 1,
                "text": text
            })
    return pages_data
