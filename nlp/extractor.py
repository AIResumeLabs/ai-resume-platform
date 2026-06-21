import os
import re
import json
import logging
from google import genai
from google.genai import types

# Initialize logger
logger = logging.getLogger(__name__)
client = genai.Client()
# Initialize the Gemini client (Make sure GEMINI_API_KEY is in your environment variables)


def extract_entities_with_llm(text: str) -> dict:
    """
    Uses Gemini with strict JSON schema execution to extract candidate contact
    details and any technical skills natively found inside the text profile.
    """
    
    prompt = f"""

    You are an expert technical recruitment parser. Analyze the following raw resume text and extract:
    1. Candidate Name (Look at the top of the resume).
    2. Candidate Email address.
    3. Candidate Phone number.
    4. An exhaustive list of technical skills, frameworks, tools, libraries, mathematical methods, 
       programming languages, and professional platforms (like Codeforces, LeetCode, etc.) explicitly mentioned.
    
    Standardize all technical skills to their common industry naming conventions (e.g., convert "cpp" or "c plus plus" to "C++", "python3" to "Python", "stats" to "Statistics").

    Raw Resume Text:
    ---
    {text}
    ---
    """

    try:
        # Enforce structural integrity using Response Schema
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "name": types.Schema(type=types.Type.STRING, description="Full name of candidate"),
                        "email": types.Schema(type=types.Type.STRING, description="Email address"),
                        "phone": types.Schema(type=types.Type.STRING, description="Phone number"),
                        "skills": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING),
                            description="Extracted industry-standard technical skills"
                        )
                    },
                    required=["name", "email", "phone", "skills"]
                )
            )
        )
        
        # Parse the strictly structured JSON text response
        parsed_data = json.loads(response.text)
        return parsed_data

    except Exception as e:
        logger.error(f"LLM extraction layer failed: {str(e)}")
        # Graceful fallback to regex parsing to prevent pipeline breakages
        return {
            "name": "Unknown Candidate",
            "email": extract_email_fallback(text),
            "phone": extract_phone_fallback(text),
            "skills": []
        }

# ==============================================================================
# DETERMINISTIC REGEX FALLBACKS (Runs only if API call fails)
# ==============================================================================
def extract_email_fallback(text: str) -> str | None:
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_phone_fallback(text: str) -> str | None:
    pattern = r'(?:\+?91[- ]?)?[6-9]\d{9}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

# ==============================================================================
# MAIN SYSTEM INTERFACE
# ==============================================================================
def parse_resume_text(text: str) -> dict:
    """
    Orchestrates parsing by replacing spaCy processing entirely with 
    the dynamic LLM extraction layer.
    """
    if not text or not text.strip():
        return {"name": "Empty Document", "email": None, "phone": None, "skills": []}
        
    logger.info("Routing extraction pipeline execution directly to Gemini layer...")
    extracted_data = extract_entities_with_llm(text)
    
    return extracted_data