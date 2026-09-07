import pdfplumber
from typing import List, Dict

def parse_pdf(file_path: str) -> List[Dict]:
    pages_data = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            # Extract tables
            tables = page.extract_tables()
            table_markdowns = []
            for table in tables:
                if not table: continue
                md_table = []
                for row in table:
                    # Clean newlines from cells
                    cleaned_row = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
                    md_table.append("| " + " | ".join(cleaned_row) + " |")
                    
                # Add separator after header
                if len(md_table) > 0:
                    header_len = len(table[0])
                    separator = "| " + " | ".join(["---"] * header_len) + " |"
                    md_table.insert(1, separator)
                
                table_markdowns.append("\n".join(md_table))
            
            # Combine text and tables
            if table_markdowns:
                text += "\n\n[Extracted Tables]:\n\n" + "\n\n".join(table_markdowns)
                
            pages_data.append({
                "page_number": i + 1,
                "text": text
            })
    return pages_data
