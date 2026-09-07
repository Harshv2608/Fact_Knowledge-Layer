from typing import List, Dict

def chunk_text(pages: List[Dict], chunk_size: int = 1500, overlap: int = 200) -> List[Dict]:
    """
    Semantic chunker. Splits by double newline (paragraphs/tables)
    to keep tables and their footnotes intact.
    """
    chunks = []
    chunk_index = 0
    
    for page in pages:
        text = page["text"]
        blocks = text.split("\n\n")
        
        current_chunk_text = ""
        
        for block in blocks:
            if len(current_chunk_text) + len(block) > chunk_size and len(current_chunk_text) > 0:
                chunks.append({
                    "page_number": page["page_number"],
                    "chunk_index": chunk_index,
                    "text": current_chunk_text.strip()
                })
                chunk_index += 1
                
                current_chunk_text = block + "\n\n"
            else:
                current_chunk_text += block + "\n\n"
                
        if current_chunk_text.strip():
            chunks.append({
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
                "text": current_chunk_text.strip()
            })
            chunk_index += 1
            
    return chunks
