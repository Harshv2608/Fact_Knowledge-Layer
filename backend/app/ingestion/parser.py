import fitz  # PyMuPDF

def parse_pdf(file_path: str):
    """
    Parses a PDF file and returns a list of dictionaries containing page text and metadata.
    """
    pages_data = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        # simple cleaning
        text = " ".join(text.split())
        if text.strip():
            pages_data.append({
                "page_number": page_num + 1,
                "text": text.strip()
            })
    return pages_data
