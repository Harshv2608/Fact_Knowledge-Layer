from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import os
import shutil
from app.db.session import get_db, SessionLocal
from app.models.database import Document, DocumentPage, Chunk, Fact, Evidence
from app.ingestion.parser import parse_pdf
from app.ingestion.chunker import chunk_text
from app.extraction.llm_extractor import extract_facts_from_chunk
from app.retrieval.embedder import get_embedding
from app.normalization.normalizer import normalize_value

router = APIRouter()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_document_background(document_id: int, file_path: str):
    db = SessionLocal()
    db_doc = db.query(Document).filter(Document.id == document_id).first()
    if not db_doc:
        db.close()
        return

    try:
        print(f"[{document_id}] Starting processing for {file_path}")
        # Parse PDF
        db_doc.processing_status = "PARSING"
        db.commit()
        print(f"[{document_id}] Parsing PDF...")
        pages_data = parse_pdf(file_path)
        print(f"[{document_id}] Parsed {len(pages_data)} pages.")
        
        db_pages = []
        for page_data in pages_data:
            db_page = DocumentPage(
                document_id=db_doc.id,
                page_number=page_data["page_number"],
                text=page_data["text"]
            )
            db.add(db_page)
            db_pages.append(db_page)
        db.commit()
        print(f"[{document_id}] Saved pages to DB.")
        
        # Chunk text
        print(f"[{document_id}] Chunking text...")
        chunks_data = chunk_text(pages_data, chunk_size=1000, overlap=200) # larger chunks for markdown
        print(f"[{document_id}] Generated {len(chunks_data)} chunks.")
        
        page_num_to_id = {p.page_number: p.id for p in db_pages}
        
        print(f"[{document_id}] Generating embeddings for chunks...")
        for i, chunk_data in enumerate(chunks_data):
            db_chunk = Chunk(
                document_id=db_doc.id,
                page_id=page_num_to_id.get(chunk_data["page_number"]),
                chunk_index=chunk_data["chunk_index"],
                text=chunk_data["text"],
                embedding=get_embedding(chunk_data["text"])
            )
            db.add(db_chunk)
            if i % 10 == 0:
                print(f"[{document_id}] Embedded {i}/{len(chunks_data)} chunks.")
            
        db_doc.processing_status = "PARSED"
        db.commit()
        print(f"[{document_id}] Status set to PARSED.")
        
        # Extract facts
        db_doc.processing_status = "EXTRACTING"
        db.commit()
        print(f"[{document_id}] Status set to EXTRACTING. Starting LLM...")
        
        chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
        # Brownie Point: Handle large PDFs without significant performance issues
        # Parallelize LLM extraction to speed up large documents
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        results = []
        
        # Use 3 workers to match the 3 API keys for parallel extraction
        with ThreadPoolExecutor(max_workers=3) as executor:
            def extract_with_delay(text, title):
                time.sleep(2) # 2 seconds delay per worker; with 3 keys ~30 RPM total (10 RPM per key)
                return extract_facts_from_chunk(text, title)
                
            future_to_chunk = {
                executor.submit(extract_with_delay, chunk.text, db_doc.title): chunk 
                for chunk in chunks
            }
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    extracted_facts = future.result()
                    results.append((chunk, extracted_facts))
                except Exception as exc:
                    print(f"Chunk extraction generated an exception: {exc}")
                    
        for chunk, extracted_facts in results:
            for f_data in extracted_facts:
                if f_data["evidence"] not in chunk.text:
                    continue
                    
                fact_text = f"{f_data['subject']} {f_data['predicate']} {f_data.get('raw_value', '')} {f_data.get('time_context', '')}"
                
                db_fact = Fact(
                    subject=f_data["subject"],
                    predicate=f_data["predicate"],
                    raw_value=f_data.get("raw_value"),
                    raw_unit=f_data.get("raw_unit"),
                    normalized_numeric_value=f_data.get("normalized_numeric_value") or normalize_value(f_data.get("raw_value", ""), f_data.get("raw_unit", "")),
                    normalized_scale=f_data.get("normalized_scale"),
                    normalized_currency=f_data.get("normalized_currency"),
                    sign_convention_applied=f_data.get("sign_convention_applied"),
                    time_context=f_data.get("time_context"),
                    scope=f_data.get("scope"),
                    geography=f_data.get("geography"),
                    qualifiers=f_data.get("qualifiers"),
                    confidence=f_data.get("confidence", 0.0),
                    embedding=get_embedding(fact_text)
                )
                db.add(db_fact)
                db.flush()
                
                db_evidence = Evidence(
                    fact_id=db_fact.id,
                    document_id=document_id,
                    page_id=chunk.page_id,
                    chunk_id=chunk.id,
                    evidence_text=f_data["evidence"]
                )
                db.add(db_evidence)
                
        db_doc.processing_status = "EXTRACTED"
        db.commit()
        
    except Exception as e:
        db_doc.processing_status = "ERROR"
        db.commit()
        print(f"Error processing document: {e}")
    finally:
        db.close()
        # Clean up temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Failed to delete temp file {file_path}: {e}")

@router.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    import werkzeug.utils
    import filetype
    
    secure_filename = werkzeug.utils.secure_filename(file.filename)
    if not secure_filename.endswith(".pdf") or file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed and filename must be valid")
        
    # Magic byte validation
    header = await file.read(2048)
    kind = filetype.guess(header)
    if kind is None or kind.mime != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. File does not match PDF magic bytes.")
        
    await file.seek(0)
        
    file_path = os.path.join(UPLOAD_DIR, secure_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    db_doc = Document(filename=secure_filename, title=secure_filename, processing_status="PENDING")
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    background_tasks.add_task(process_document_background, db_doc.id, file_path)
    
    return {"document_id": db_doc.id, "filename": db_doc.filename, "status": "Success", "message": "Document is being processed in the background."}

@router.get("/")
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return [{"id": d.id, "filename": d.filename, "status": d.processing_status, "uploaded_at": d.uploaded_at} for d in docs]

@router.post("/{document_id}/extract")
def extract_facts_for_document(document_id: int, db: Session = Depends(get_db)):
    # This endpoint is now redundant as extraction happens automatically, but we can keep it to retry manually
    db_doc = db.query(Document).filter(Document.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # We could trigger the background task again here, but for simplicity we return a message
    return {"status": "Success", "message": "Extraction runs automatically upon upload in the new architecture."}
