from google import genai
from pydantic import BaseModel, Field
import os
import time
import threading
from typing import List, Optional

class FactSchema(BaseModel):
    subject: str = Field(description="The entity or subject the fact is about")
    predicate: str = Field(description="The property or action related to the subject")
    raw_value: str = Field(description="The exact raw string value, object, or claim from the text")
    raw_unit: Optional[str] = Field(description="Exact raw unit string if applicable", default=None)
    time_context: Optional[str] = Field(description="Time period or date if mentioned", default=None)
    scope: Optional[str] = Field(description="Scope or category", default=None)
    geography: Optional[str] = Field(description="Geography", default=None)
    qualifiers: Optional[str] = Field(description="Other context like footnotes, 'y-o-y', 'net'", default=None)
    sign_convention_applied: Optional[str] = Field(description="If a table footnote defines a sign convention (e.g., '-' signifies inflow), extract it here.", default=None)
    confidence: float = Field(description="Extraction confidence from 0.0 to 1.0")
    evidence: str = Field(description="Exact substring from the text that proves this fact.")

class FactExtractionResponse(BaseModel):
    facts: list[FactSchema]

# --- Multi-key client pool ---
# Load all available API keys from environment
_api_keys = []
for key_env in ["GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
    key = os.getenv(key_env)
    if key and key != "your_gemini_api_key_here":
        _api_keys.append(key)

# Fallback to single GEMINI_API_KEY if the numbered keys aren't set
if not _api_keys:
    fallback = os.getenv("GEMINI_API_KEY", "")
    if fallback and fallback != "your_gemini_api_key_here":
        _api_keys.append(fallback)

# Create a client pool — one client per API key
_clients = [genai.Client(api_key=k) for k in _api_keys] if _api_keys else []
_client_index = 0
_client_lock = threading.Lock()

def _get_next_client():
    """Round-robin client selection across API keys (thread-safe)."""
    global _client_index
    if not _clients:
        return None
    with _client_lock:
        client = _clients[_client_index % len(_clients)]
        _client_index += 1
        return client

def extract_facts_from_chunk(text: str, document_title: str) -> List[dict]:
    if os.getenv("MOCK_LLM") == "1" or not _clients:
        # Mock logic if API key isn't provided or MOCK_LLM is enabled, to prevent consuming tokens during tests
        return [{
            "subject": "Mock Subject",
            "predicate": "Mock Predicate",
            "raw_value": "123",
            "raw_unit": "%",
            "time_context": "2024",
            "scope": "National",
            "geography": "India",
            "qualifiers": "Mock qualifier",
            "sign_convention_applied": None,
            "confidence": 0.9,
            "evidence": text[:100] if len(text) > 100 else text
        }]
        
    prompt = f"""
You are a highly accurate Fact Extraction system.
Extract all meaningful macroeconomic, financial, or semantic facts from the following text chunk.
This chunk is from a document titled '{document_title}'.

RULES:
1. Extract numerical and key semantic facts.
2. The 'evidence' field MUST be an exact substring from the text provided below. Do NOT alter the evidence text.
3. If a fact has no clear evidence in the text, do not extract it.
4. Capture all relevant context (time, scope, geography, qualifiers) to ensure the fact is unambiguous.
5. If the text is a table and includes footnotes about sign conventions (e.g., "-" signifies inflow), extract that exactly into 'sign_convention_applied'.

OUTPUT FORMAT:
Respond ONLY with a valid JSON array of objects. Do not include markdown code blocks. Each object must have these exact string keys:
- subject
- predicate
- raw_value
- raw_unit (or null)
- time_context (or null)
- scope (or null)
- geography (or null)
- qualifiers (or null)
- sign_convention_applied (or null)
- confidence (number 0.0 to 1.0)
- evidence

Text Chunk:
{text}
"""
    import json
    client = _get_next_client()
    if not client:
        print(f"[LLM] No API client available, returning empty.")
        return []
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'temperature': 0.1,
                },
            )
            # Clean possible markdown block
            text_resp = response.text.strip()
            if text_resp.startswith("```json"):
                text_resp = text_resp[7:]
            if text_resp.endswith("```"):
                text_resp = text_resp[:-3]
            
            parsed = json.loads(text_resp.strip())
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "facts" in parsed:
                return parsed["facts"]
            return []
        except Exception as e:
            print(f"[LLM] Extraction error (attempt {attempt+1}/3): {e}")
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                # Rate limited — wait longer and try with a different client
                wait_time = 5 * (2 ** attempt)
                print(f"[LLM] Rate limited. Waiting {wait_time}s before retry with different key...")
                time.sleep(wait_time)
                client = _get_next_client()
            else:
                time.sleep(2 ** attempt)
            
    return []
