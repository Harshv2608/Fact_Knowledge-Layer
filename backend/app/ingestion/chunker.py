from typing import List, Dict

def chunk_text(pages: List[Dict], chunk_size: int = 2000, overlap: int = 400) -> List[Dict]:
    """
    Chunks text by character limits, but attempts to split at newlines to preserve 
    lines. Increased chunk size ensures tables and associated footnotes stay together.
    """
    chunks = []
    chunk_index = 0
    
    for page in pages:
        text = page["text"]
        
        start = 0
        while start < len(text):
            end = start + chunk_size
            
            # If we're not at the end of the text, try to find a newline to split on cleanly
            if end < len(text):
                # Try to find a double newline first
                last_double_newline = text.rfind("\n\n", start, end)
                if last_double_newline != -1 and last_double_newline > start + chunk_size // 2:
                    end = last_double_newline + 2
                else:
                    # Fallback to single newline
                    last_newline = text.rfind("\n", start, end)
                    if last_newline != -1 and last_newline > start + chunk_size // 2:
                        end = last_newline + 1
            
            chunk_text_slice = text[start:end].strip()
            if chunk_text_slice:
                chunks.append({
                    "page_number": page["page_number"],
                    "chunk_index": chunk_index,
                    "text": chunk_text_slice
                })
                chunk_index += 1
                
            start = end - overlap
            
    return chunks
