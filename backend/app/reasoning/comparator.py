from google import genai
from pydantic import BaseModel, Field
import os
import time

class RelationshipOutput(BaseModel):
    relationship_type: str = Field(description="One of: CORROBORATES, CONTRADICTS, RECONCILES, UNRELATED")
    confidence: float = Field(description="Confidence from 0.0 to 1.0")
    explanation: str = Field(description="Explanation of why this relationship holds")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def compare_facts(fact_a: dict, fact_b: dict) -> dict:
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        return {"relationship_type": "UNRELATED", "confidence": 0.0, "explanation": "Mocked due to missing API key"}

    prompt = f"""
Compare the following two extracted facts and determine their relationship.
Relationship must be one of: CORROBORATES, CONTRADICTS, RECONCILES, UNRELATED.

Fact A:
- Subject: {fact_a.get('subject')}
- Predicate: {fact_a.get('predicate')}
- Value: {fact_a.get('object_value')} ({fact_a.get('unit')})
- Time Context: {fact_a.get('time_context')}
- Scope: {fact_a.get('scope')}
- Geography: {fact_a.get('geography')}
- Qualifiers: {fact_a.get('qualifiers')}

Fact B:
- Subject: {fact_b.get('subject')}
- Predicate: {fact_b.get('predicate')}
- Value: {fact_b.get('object_value')} ({fact_b.get('unit')})
- Time Context: {fact_b.get('time_context')}
- Scope: {fact_b.get('scope')}
- Geography: {fact_b.get('geography')}
- Qualifiers: {fact_b.get('qualifiers')}

First, determine if they refer to the same underlying proposition.
If they do, are they saying the same thing (CORROBORATES), conflicting (CONTRADICTS), or do they appear conflicting but are explained by their context like different time periods or units (RECONCILES)?
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
