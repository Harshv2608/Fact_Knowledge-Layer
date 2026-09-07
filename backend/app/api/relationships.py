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
    
    for fact_a in facts:
        if fact_a.embedding is None:
            continue
            
        # Get document_id for fact_a to ensure cross-document comparison
        ev_a = db.query(Evidence).filter(Evidence.fact_id == fact_a.id).first()
        if not ev_a:
            continue
        doc_a_id = ev_a.document_id
            
        similar_facts = db.query(Fact).filter(
            Fact.id != fact_a.id
        ).order_by(Fact.embedding.cosine_distance(fact_a.embedding)).limit(5).all()
        
        for fact_b in similar_facts:
            ev_b = db.query(Evidence).filter(Evidence.fact_id == fact_b.id).first()
            if not ev_b or ev_b.document_id == doc_a_id:
                continue # Skip same document
                
            # Check if relationship already exists
            exists = db.query(Relationship).filter(
                ((Relationship.fact_a_id == fact_a.id) & (Relationship.fact_b_id == fact_b.id)) |
                ((Relationship.fact_a_id == fact_b.id) & (Relationship.fact_b_id == fact_a.id))
            ).first()
            
            if exists:
                continue
                
            res = compare_facts(
                {
                    "subject": fact_a.subject, "predicate": fact_a.predicate, "object_value": fact_a.object_value,
                    "unit": fact_a.unit, "time_context": fact_a.time_context, "scope": fact_a.scope,
                    "geography": fact_a.geography, "qualifiers": fact_a.qualifiers
                },
                {
                    "subject": fact_b.subject, "predicate": fact_b.predicate, "object_value": fact_b.object_value,
                    "unit": fact_b.unit, "time_context": fact_b.time_context, "scope": fact_b.scope,
                    "geography": fact_b.geography, "qualifiers": fact_b.qualifiers
                }
            )
            
            if res["relationship_type"] in ["CORROBORATES", "CONTRADICTS", "RECONCILES"]:
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
