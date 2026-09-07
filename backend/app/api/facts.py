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
            "object_value": f.object_value,
            "unit": f.unit,
            "time_context": f.time_context,
            "scope": f.scope,
            "geography": f.geography,
            "qualifiers": f.qualifiers,
            "confidence": f.confidence,
            "evidence": evs
        })
    return out
