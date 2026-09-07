from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import shutil
from app.db.session import get_db
from app.models.database import Document, DocumentPage, Chunk, Fact, Evidence
from app.ingestion.parser import parse_pdf
from app.ingestion.chunker import chunk_text
from app.extraction.llm_extractor import extract_facts_from_chunk
from app.retrieval.embedder import get_embedding
from app.normalization.normalizer import normalize_value

router = APIRouter()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    import werkzeug.utils
    secure_filename = werkzeug.utils.secure_filename(file.filename)
    if not secure_filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed and filename must be valid")
        
    file_path = os.path.join(UPLOAD_DIR, secure_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create document record
    db_doc = Document(filename=secure_filename, title=secure_filename, processing_status="PARSING")
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    try:
        # Parse PDF
        pages_data = parse_pdf(file_path)
        
        # Save pages to DB
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
        
        # Chunk text
        chunks_data = chunk_text(pages_data, chunk_size=500, overlap=100)
        
        # Save chunks to DB
        # To link chunk to page_id, we need page mapping
        page_num_to_id = {p.page_number: p.id for p in db_pages}
        
        for chunk_data in chunks_data:
            db_chunk = Chunk(
                document_id=db_doc.id,
                page_id=page_num_to_id.get(chunk_data["page_number"]),
                chunk_index=chunk_data["chunk_index"],
                text=chunk_data["text"],
                embedding=get_embedding(chunk_data["text"])
            )
            db.add(db_chunk)
            
        db_doc.processing_status = "PARSED"
        db.commit()
        
        return {"document_id": db_doc.id, "filename": db_doc.filename, "status": "Success", "pages": len(pages_data), "chunks": len(chunks_data)}
    
    except Exception as e:
        db_doc.processing_status = "ERROR"
        db.commit()
        # Log the actual error, but don't leak it to the client
        print(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during document processing.")

@router.get("/")
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return [{"id": d.id, "filename": d.filename, "status": d.processing_status, "uploaded_at": d.uploaded_at} for d in docs]

@router.post("/{document_id}/extract")
def extract_facts_for_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
    
    total_facts = 0
    
    for chunk in chunks:
        extracted_facts = extract_facts_from_chunk(chunk.text, doc.title)
        
        for f_data in extracted_facts:
            # Check if evidence matches text exactly
            if f_data["evidence"] not in chunk.text:
                continue # Skip hallucinated evidence
                
            fact_text = f"{f_data['subject']} {f_data['predicate']} {f_data['object_value']} {f_data['time_context'] or ''}"
            
            db_fact = Fact(
                subject=f_data["subject"],
                predicate=f_data["predicate"],
                object_value=f_data["object_value"],
                value_type=f_data["value_type"],
                unit=f_data["unit"],
                normalized_value=f_data.get("normalized_value") or normalize_value(f_data.get("object_value", ""), f_data.get("unit", "")),
                time_context=f_data["time_context"],
                scope=f_data["scope"],
                geography=f_data["geography"],
                qualifiers=f_data["qualifiers"],
                confidence=f_data["confidence"],
                embedding=get_embedding(fact_text)
            )
            db.add(db_fact)
            db.flush() # get fact id
            
            db_evidence = Evidence(
                fact_id=db_fact.id,
                document_id=document_id,
                page_id=chunk.page_id,
                chunk_id=chunk.id,
                evidence_text=f_data["evidence"]
            )
            db.add(db_evidence)
            total_facts += 1
            
    doc.processing_status = "EXTRACTED"
    db.commit()
    
    return {"status": "Success", "extracted_facts": total_facts}
