import os
import requests
import json

HF_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
HF_TOKEN = os.environ.get("HF_TOKEN")

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

EXTRACTION_SYSTEM = """You are an expert claims intake assistant. Output STRICT JSON ONLY.
Schema:
{
 "claimant_name": "string|null",
 "contact_phone": "string|null",
 "policy_number": "string|null",
 "incident_datetime": "string|null",
 "incident_location": "string|null",
 "incident_description": "string",
 "claimed_amount": "number|null",
 "metadata": { "detected_entities": ["string"] }
}
If unsure, use null. No commentary. JSON only.
"""

CLASSIFY_SYSTEM = """You are a claims adjudication assistant. Output STRICT JSON ONLY.
Schema:
{
 "label": "valid"|"invalid"|"fraudulent",
 "score": 0.0-1.0,
 "rationale": "string",
 "policy_flags": ["string"],
 "suggested_next_steps": ["string"]
}
JSON only.
"""


def _hf_generate(prompt: str):
    """Generate text using HuggingFace Inference API"""
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.2,
            "return_full_text": False,
        },
    }
    try:
        r = requests.post(HF_URL, headers=HEADERS, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        # Handle different response formats
        if isinstance(data, list) and data and "generated_text" in data[0]:
            return data[0]["generated_text"]
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]
        if isinstance(data, str):
            return data
        return json.dumps(data)
    except Exception as e:
        print(f"HF API Error: {e}")
        raise


def extract_entities(transcript: str) -> dict:
    """Extract structured entities from claim transcript"""
    prompt = f"""<|system|>
{EXTRACTION_SYSTEM}
<|user|>
Transcript:
\"\"\"
{transcript}
\"\"\"
Return JSON only."""

    try:
        raw = _hf_generate(prompt)
        # Try to extract JSON from response
        # Remove markdown code blocks if present
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        return json.loads(raw)
    except Exception as e:
        print(f"Extraction error: {e}")
        # Return fallback structure
        return {
            "claimant_name": None,
            "contact_phone": None,
            "policy_number": None,
            "incident_datetime": None,
            "incident_location": None,
            "incident_description": transcript[:500],
            "claimed_amount": None,
            "metadata": {"detected_entities": [], "error": str(e)},
        }


def classify_claim(extracted: dict, transcript: str) -> dict:
    """Classify claim as valid/invalid/fraudulent with rationale"""
    prompt = f"""<|system|>
{CLASSIFY_SYSTEM}
<|user|>
Data:
{json.dumps(extracted, ensure_ascii=False)}

Transcript:
\"\"\"
{transcript}
\"\"\"
Return JSON only."""

    try:
        raw = _hf_generate(prompt)
        # Try to extract JSON from response
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        return json.loads(raw)
    except Exception as e:
        print(f"Classification error: {e}")
        # Return fallback classification
        return {
            "label": "invalid",
            "score": 0.5,
            "rationale": "Unable to classify due to processing error",
            "policy_flags": ["processing_error"],
            "suggested_next_steps": ["manual_review"],
        }
