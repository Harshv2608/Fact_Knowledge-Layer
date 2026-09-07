from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Fact

router = APIRouter()

@router.get("/")
def get_facts(db: Session = Depends(get_db)):
    facts = db.query(Fact).all()
    out = []
    for f in facts:
        # Include evidence
        evs = [ev.evidence_text for ev in f.evidence_links]
        out.append({
            "id": f.id,
            "subject": f.subject,
            "predicate": f.predicate,
            "raw_value": f.raw_value,
            "raw_unit": f.raw_unit,
            "normalized_numeric_value": f.normalized_numeric_value,
            "normalized_scale": f.normalized_scale,
            "normalized_currency": f.normalized_currency,
            "time_context": f.time_context,
            "scope": f.scope,
            "geography": f.geography,
            "sign_convention_applied": f.sign_convention_applied,
            "confidence": f.confidence,
            "evidence": evs
        })
    return out
