def chunk_text(pages_data, chunk_size=500, overlap=100):
    """
    Chunks text while preserving page number provenance.
    For simplicity, we chunk page by page. If a page is too long, we split it.
    """
    chunks = []
    chunk_index = 0
    
    for page in pages_data:
        page_num = page["page_number"]
        text = page["text"]
        
        words = text.split()
        if not words:
            continue
            
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "chunk_index": chunk_index,
                "page_number": page_num,
                "text": chunk_text
            })
            chunk_index += 1
            
            if end >= len(words):
                break
            start += (chunk_size - overlap)
            
    return chunks
