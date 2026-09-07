from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Fact, Relationship, Evidence
from app.reasoning.comparator import compare_facts

router = APIRouter()

@router.post("/compute")
def compute_relationships(db: Session = Depends(get_db)):
    facts = db.query(Fact).all()
    count = 0
    
    # Pre-fetch evidence to map fact_id -> doc_id
    evidences = db.query(Evidence).all()
    fact_doc_map = {ev.fact_id: ev.document_id for ev in evidences}
    
    # Pre-fetch existing relationships
    existing_rels = db.query(Relationship).all()
    existing_pairs = set()
    for rel in existing_rels:
        existing_pairs.add((rel.fact_a_id, rel.fact_b_id))
        existing_pairs.add((rel.fact_b_id, rel.fact_a_id))
        
    for fact_a in facts:
        if fact_a.embedding is None:
            continue
            
        doc_a_id = fact_doc_map.get(fact_a.id)
        if not doc_a_id:
            continue
            
        # Top 5 similar
        similar_facts = db.query(Fact).filter(
            Fact.id != fact_a.id
        ).order_by(Fact.embedding.cosine_distance(fact_a.embedding)).limit(5).all()
        
        for fact_b in similar_facts:
            doc_b_id = fact_doc_map.get(fact_b.id)
            if not doc_b_id or doc_b_id == doc_a_id:
                continue # Skip same document
                
            if (fact_a.id, fact_b.id) in existing_pairs:
                continue
                
            res = compare_facts(
                {
                    "subject": fact_a.subject, "predicate": fact_a.predicate, "raw_value": fact_a.raw_value,
                    "raw_unit": fact_a.raw_unit, "normalized_numeric_value": fact_a.normalized_numeric_value,
                    "time_context": fact_a.time_context, "scope": fact_a.scope,
                    "geography": fact_a.geography, "qualifiers": fact_a.qualifiers,
                    "sign_convention_applied": fact_a.sign_convention_applied
                },
                {
                    "subject": fact_b.subject, "predicate": fact_b.predicate, "raw_value": fact_b.raw_value,
                    "raw_unit": fact_b.raw_unit, "normalized_numeric_value": fact_b.normalized_numeric_value,
                    "time_context": fact_b.time_context, "scope": fact_b.scope,
                    "geography": fact_b.geography, "qualifiers": fact_b.qualifiers,
                    "sign_convention_applied": fact_b.sign_convention_applied
                }
            )
            
            existing_pairs.add((fact_a.id, fact_b.id))
            existing_pairs.add((fact_b.id, fact_a.id))
            
            if res["relationship_type"] in ["CORROBORATES", "CONTRADICTS", "RECONCILES", "UNCERTAIN"]:
                rel = Relationship(
                    fact_a_id=fact_a.id,
                    fact_b_id=fact_b.id,
                    relationship_type=res["relationship_type"],
                    confidence=res["confidence"],
                    explanation=res["explanation"]
                )
                db.add(rel)
                db.commit()
                count += 1
                
    return {"status": "Success", "relationships_created": count}

@router.get("/")
def get_relationships(db: Session = Depends(get_db)):
    rels = db.query(Relationship).all()
    out = []
    for r in rels:
        out.append({
            "id": r.id,
            "fact_a_id": r.fact_a_id,
            "fact_b_id": r.fact_b_id,
            "relationship_type": r.relationship_type,
            "confidence": r.confidence,
            "explanation": r.explanation
        })
    return out
