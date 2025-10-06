import re
from langchain_huggingface import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from transformers import pipeline

try:
    hf_pipeline = pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
        device=-1,
        max_length=256,
    )
    llm = HuggingFacePipeline(pipeline=hf_pipeline)
except Exception as e:
    print(f"Failed to load LLM: {e}")
    llm = None


def extract_entities(transcript: str) -> dict:
    """Extract entities using LangChain prompt chaining (Step 1)

    This demonstrates pure LLM-based extraction using LangChain's prompt chaining.
    Each field is extracted via a separate prompt to the LLM, showing the power
    of prompt engineering for information extraction.
    """
    print("LangChain: Extracting entities via prompt chaining...")

    if not llm:
        print("LangChain: ERROR - LLM not initialized, falling back to minimal extraction")
        return {
            "claimant_name": None,
            "contact_phone": None,
            "policy_number": None,
            "incident_datetime": None,
            "incident_location": None,
            "incident_description": transcript[:200],
            "claimed_amount": None,
            "metadata": {"detected_entities": [], "extraction_method": "llm_unavailable"}
        }

    result = {
        "claimant_name": None,
        "contact_phone": None,
        "incident_datetime": None,
        "incident_location": None,
        "incident_description": None,
        "claimed_amount": None,
        "metadata": {"detected_entities": [], "extraction_method": "langchain_pure_llm"}
    }

    # PROMPT CHAIN STEP 1: Extract claimant name
    try:
        name_prompt = PromptTemplate(
            input_variables=["text"],
            template="Extract the person's full name from this insurance claim. Only return the name, nothing else. If no name, say 'none'.\n\nClaim: {text}\n\nName:"
        )
        name_chain = name_prompt | llm
        name = name_chain.invoke({"text": transcript}).strip()
        if name and name.lower() != 'none' and len(name) < 50:
            result["claimant_name"] = name
            print(f"Name: {name}")
    except Exception as e:
        print(f"Name extraction error: {type(e).__name__}: {str(e)}")

    # PROMPT CHAIN STEP 2: Extract phone number
    try:
        phone_prompt = PromptTemplate(
            input_variables=["text"],
            template="Extract the phone number from this claim. Look for patterns like '8-777-123-4567' or '+7-777-123-4567'. Only return the phone number, nothing else. If no phone, say 'none'.\n\nClaim: {text}\n\nPhone:"
        )
        phone_chain = phone_prompt | llm
        phone = phone_chain.invoke({"text": transcript}).strip()
        if phone and phone.lower() != 'none' and len(phone) < 30:
            # Validate it actually appears in the transcript (prevent hallucination)
            phone_clean = phone.replace(" ", "").replace("-", "")
            transcript_clean = transcript.replace(" ", "").replace("-", "")
            if phone_clean in transcript_clean or phone in transcript:
                result["contact_phone"] = phone
                print(f"Phone: {phone}")
            else:
                print(f"Phone hallucination prevented: {phone}")
    except Exception as e:
        print(f"Phone extraction error: {type(e).__name__}: {str(e)}")

    # PROMPT CHAIN STEP 3: Extract incident date
    try:
        date_prompt = PromptTemplate(
            input_variables=["text"],
            template="What date did the incident occur? Extract only the date from this text. If no date, say 'none'.\n\nText: {text}\n\nDate:"
        )
        date_chain = date_prompt | llm
        date = date_chain.invoke({"text": transcript}).strip()
        if date and date.lower() != 'none' and len(date) < 50:
            result["incident_datetime"] = date
            print(f"Date: {date}")
    except Exception as e:
        print(f"Date extraction error: {type(e).__name__}: {str(e)}")

    # PROMPT CHAIN STEP 4: Extract location
    try:
        location_prompt = PromptTemplate(
            input_variables=["text"],
            template="What city or location is mentioned in this claim? Extract only the location name. If none, say 'none'.\n\nClaim: {text}\n\nLocation:"
        )
        location_chain = location_prompt | llm
        location = location_chain.invoke({"text": transcript}).strip()
        if location and location.lower() != 'none' and len(location) < 50:
            result["incident_location"] = location
            print(f"Location: {location}")
    except Exception as e:
        print(f"Location extraction error: {type(e).__name__}: {str(e)}")

    # PROMPT CHAIN STEP 5: Extract claimed amount
    try:
        amount_prompt = PromptTemplate(
            input_variables=["text"],
            template="What is the claimed amount in this insurance claim? Look for money amounts in KZT (Kazakhstan Tenge) or other currencies. Only return the number without currency symbols. If no amount, say 'none'.\n\nClaim: {text}\n\nAmount:"
        )
        amount_chain = amount_prompt | llm
        amount_str = amount_chain.invoke({"text": transcript}).strip()
        if amount_str and amount_str.lower() != 'none':
            # Clean and convert to float
            amount_clean = re.sub(r'[^\d,.]', '', amount_str).replace(',', '')
            if amount_clean:
                try:
                    result["claimed_amount"] = float(amount_clean)
                    print(f"Amount: {result['claimed_amount']}")
                except ValueError:
                    print(f"Amount conversion failed: {amount_str}")
    except Exception as e:
        print(f"Amount extraction error: {type(e).__name__}: {str(e)}")

    # PROMPT CHAIN STEP 6: Generate description summary
    try:
        desc_prompt = PromptTemplate(
            input_variables=["text"],
            template="Summarize what happened in this insurance claim in one clear sentence.\n\nClaim: {text}\n\nSummary:"
        )
        desc_chain = desc_prompt | llm
        description = desc_chain.invoke({"text": transcript}).strip()
        if description and len(description) > 10:
            result["incident_description"] = description
            print(f"Description: {description[:60]}...")
        else:
            result["incident_description"] = transcript[:200]
            print("Description fallback to transcript")
    except Exception as e:
        print(f"Description error: {type(e).__name__}: {str(e)}")
        result["incident_description"] = transcript[:200]

    # Update metadata
    result["metadata"]["detected_entities"] = [
        k for k, v in result.items()
        if k not in ["metadata", "incident_description"] and v is not None
    ]

    print(f"LangChain: Extracted {len(result['metadata']['detected_entities'])} fields using 6-step prompt chain")
    return result


def classify_claim(extracted: dict, transcript: str) -> dict:
    """Classify claim validity and detect fraud.

    See CLASSIFICATION_LOGIC.md for detailed documentation.
    """
    missing_count = 0
    required_fields = ["claimant_name", "incident_datetime", "claimed_amount"]
    missing_fields = []

    for field in required_fields:
        if not extracted.get(field):
            missing_count += 1
            missing_fields.append(field)

    score = 1.0
    score -= (missing_count * 0.25)
    flags = []

    if not extracted.get("claimant_name"):
        flags.append("missing_claimant_name")
    if not extracted.get("claimed_amount"):
        flags.append("missing_amount")
    if not extracted.get("incident_datetime"):
        flags.append("missing_date")

    try:
        fraud_prompt = PromptTemplate(
            input_variables=["text"],
            template="""Analyze this insurance claim for fraud indicators. Answer with YES or NO for each:
1. Does the caller not remember important details?
2. Are documents missing or lost?
3. Is someone calling on behalf of someone else?

Claim: {text}

Answer (YES/NO for each line):"""
        )
        fraud_chain = fraud_prompt | llm
        fraud_analysis = fraud_chain.invoke({"text": transcript}).strip().lower()

        if "yes" in fraud_analysis:
            if "not remember" in fraud_analysis or "don't know" in transcript.lower():
                flags.append("memory_issues")
                score -= 0.3
            if "documents missing" in fraud_analysis or ("lost" in transcript.lower() and "documents" in transcript.lower()):
                flags.append("missing_documentation")
                score -= 0.2
            if "someone else" in fraud_analysis or "friend" in transcript.lower():
                flags.append("third_party_caller")
                score -= 0.3
    except Exception:
        pass

    if score < 0.3 or len(flags) >= 3:
        label = "fraudulent"
    elif score < 0.6 or missing_count >= 3:
        label = "invalid"
    else:
        label = "valid"

    rationale = f"Completeness: {score:.1f}/1.0. "
    if missing_fields:
        rationale += f"Missing: {', '.join(missing_fields)}. "
    if flags:
        rationale += f"Flags: {', '.join(flags)}."
    else:
        rationale += "No red flags detected."

    result = {
        "label": label,
        "score": max(0.0, min(1.0, score)),
        "rationale": rationale.strip(),
        "policy_flags": flags,
        "suggested_next_steps": _get_next_steps(label, flags),
    }

    return result


def _get_next_steps(label: str, flags: list) -> list:
    if label == "fraudulent":
        return ["escalate_to_fraud_team", "request_police_report", "verify_identity"]
    elif label == "invalid":
        return ["request_missing_information", "verify_policy_coverage", "contact_claimant"]
    else:
        if flags:
            return ["verify_documents", "process_claim"]
        return ["approve_claim", "schedule_assessment"]
