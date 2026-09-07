from google import genai
from pydantic import BaseModel, Field
import os
import time
from typing import List, Optional

class FactSchema(BaseModel):
    subject: str = Field(description="The entity or subject the fact is about")
    predicate: str = Field(description="The property or action related to the subject")
    object_value: str = Field(description="The value, object, or claim")
    value_type: str = Field(description="Type of the value: NUMERICAL, PERCENTAGE, CURRENCY, SEMANTIC")
    unit: Optional[str] = Field(description="Unit if applicable (e.g., %, USD billion, crore)", default=None)
    normalized_value: Optional[float] = Field(description="Normalized float value if NUMERICAL, PERCENTAGE, or CURRENCY", default=None)
    time_context: Optional[str] = Field(description="Time period or date if mentioned (e.g., FY2024/25, March 2025)", default=None)
    scope: Optional[str] = Field(description="Scope or category (e.g., merchandise exports, retail inflation)", default=None)
    geography: Optional[str] = Field(description="Geography (e.g., India, Global)", default=None)
    qualifiers: Optional[str] = Field(description="Other context like 'First Advance Estimates', 'y-o-y', 'net'", default=None)
    confidence: float = Field(description="Extraction confidence from 0.0 to 1.0")
    evidence: str = Field(description="Exact substring from the text that proves this fact. Must match exactly.")

class FactExtractionResponse(BaseModel):
    facts: list[FactSchema]

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_facts_from_chunk(text: str, document_title: str) -> List[dict]:
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        # Mock logic if API key isn't provided, to prevent crash during testing
        return []
        
    prompt = f"""
You are a highly accurate Fact Extraction system.
Extract all meaningful macroeconomic, financial, or semantic facts from the following text chunk.
This chunk is from a document titled '{document_title}'.

RULES:
1. Extract numerical and key semantic facts.
2. The 'evidence' field MUST be an exact substring from the text provided below. Do NOT alter the evidence text.
3. If a fact has no clear evidence in the text, do not extract it.
4. Capture all relevant context (time, scope, geography, qualifiers) to ensure the fact is unambiguous.

Text Chunk:
{text}
"""
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': FactExtractionResponse,
                    'temperature': 0.1,
                },
            )
            if response.parsed:
                return [fact.model_dump() for fact in response.parsed.facts]
            break
        except Exception as e:
            print(f"Extraction error (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)
            
    return []
