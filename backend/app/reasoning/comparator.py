from google import genai
from pydantic import BaseModel, Field
import os
import time

class RelationshipOutput(BaseModel):
    relationship_type: str = Field(description="One of: CORROBORATES, CONTRADICTS, RECONCILES, UNRELATED, UNCERTAIN")
    confidence: float = Field(description="Confidence from 0.0 to 1.0")
    explanation: str = Field(description="Explanation of why this relationship holds")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "dummy_key"))

def deterministic_compare(fact_a: dict, fact_b: dict) -> dict:
    """Returns deterministic equality check results."""
    from app.normalization.normalizer import parse_time_context
    import math

    # Time match logic
    t_a = parse_time_context(fact_a.get("time_context", ""))
    t_b = parse_time_context(fact_b.get("time_context", ""))
    
    if t_a and t_b and t_a["start_year"] == t_b["start_year"]:
        time_match = True
    else:
        # Fallback to string exact match
        time_match = fact_a.get("time_context") == fact_b.get("time_context")
    
    # Value match logic
    val_a = fact_a.get("normalized_numeric_value")
    val_b = fact_b.get("normalized_numeric_value")
    
    sign_a = fact_a.get("sign_convention_applied")
    sign_b = fact_b.get("sign_convention_applied")
    
    # Apply sign inversions if footnote says so (e.g., '-' signifies inflow)
    def apply_sign_convention(val, sign_str):
        if val is not None and sign_str and "-" in sign_str and ("inflow" in sign_str.lower() or "increase" in sign_str.lower()):
            # If the value is negative but the convention says negative is an inflow, 
            # we should treat it as a positive magnitude inflow.
            return abs(val) if val < 0 else val
        return val

    val_a = apply_sign_convention(val_a, sign_a)
    val_b = apply_sign_convention(val_b, sign_b)
    
    val_match = False
    if val_a is not None and val_b is not None:
        if math.isclose(val_a, val_b, rel_tol=1e-5):
            val_match = True
            
    return {
        "time_match": time_match,
        "value_match": val_match,
        "val_a": val_a,
        "val_b": val_b,
        "sign_a": sign_a,
        "sign_b": sign_b
    }

def compare_facts(fact_a: dict, fact_b: dict) -> dict:
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        return {"relationship_type": "UNRELATED", "confidence": 0.0, "explanation": "Mocked due to missing API key"}

    det_checks = deterministic_compare(fact_a, fact_b)

    prompt = f"""
Compare the following two extracted facts and determine their relationship.
Relationship must be one of: CORROBORATES, CONTRADICTS, RECONCILES, UNRELATED, UNCERTAIN.

Fact A:
- Subject: {fact_a.get('subject')}
- Predicate: {fact_a.get('predicate')}
- Raw Value: {fact_a.get('raw_value')} {fact_a.get('raw_unit')}
- Time Context: {fact_a.get('time_context')}
- Scope/Geography: {fact_a.get('scope')} / {fact_a.get('geography')}
- Qualifiers: {fact_a.get('qualifiers')}
- Sign Convention: {fact_a.get('sign_convention_applied')}

Fact B:
- Subject: {fact_b.get('subject')}
- Predicate: {fact_b.get('predicate')}
- Raw Value: {fact_b.get('raw_value')} {fact_b.get('raw_unit')}
- Time Context: {fact_b.get('time_context')}
- Scope/Geography: {fact_b.get('scope')} / {fact_b.get('geography')}
- Qualifiers: {fact_b.get('qualifiers')}
- Sign Convention: {fact_b.get('sign_convention_applied')}

Deterministic Analysis Provided to You:
- Normalized Value Match: {det_checks['value_match']} (A: {det_checks['val_a']}, B: {det_checks['val_b']})
- Exact Time Context Match: {det_checks['time_match']}

First, determine if they refer to the same underlying proposition (semantic equivalence).
If they do:
- CORROBORATES: Deterministic value match AND same semantic proposition AND same time period/scope.
- CONTRADICTS: Same semantic proposition AND same time period/scope AND deterministic inequality AND no reconcilable context.
- RECONCILES: Same semantic proposition AND different values AND explicit contextual difference (e.g., different fiscal year, 'first advance' vs 'final', or unit difference not captured).
- UNCERTAIN: Same proposition, values differ, but no clear contextual reason.
"""
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': RelationshipOutput,
                    'temperature': 0.1,
                },
            )
            if response.parsed:
                return response.parsed.model_dump()
            break
        except Exception as e:
            print(f"Comparison error (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)
        
    return {"relationship_type": "UNRELATED", "confidence": 0.0, "explanation": "Error during comparison"}
