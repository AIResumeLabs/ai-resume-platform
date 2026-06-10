import re
import logging
import spacy
from spacy.matcher import PhraseMatcher

# Initialize logger
logger = logging.getLogger(__name__)

# Load the spaCy language model
nlp = spacy.load("en_core_web_sm")

# Baseline list of skills
SKILL_BANK = [
    "Python", "C++", "C", "Java", "JavaScript", "TypeScript",
    "FastAPI", "Flask", "Django", "Node.js", "React", "Next.js",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "ChromaDB",
    "Machine Learning", "Deep Learning", "NLP", "Data Structures", 
    "Algorithms", "Competitive Programming"
]

# --- OPTIMIZATION: Build Matcher ONCE globally on startup ---
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(skill) for skill in SKILL_BANK]
matcher.add("SKILL_LIST", patterns)


def extract_name(text: str) -> str | None:
    """Uses spaCy Named Entity Recognition (NER) to extract the first PERSON token."""
    # We restrict scanning to the first 1000 characters since names appear at the top
    doc = nlp(text[:1000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Quick sanitization to avoid catching multi-line blocks mistakenly
            name = ent.text.strip()
            if len(name.split()) <= 4:  # Rare for names to exceed 4 words
                return name
    return None


def extract_email(text: str) -> str | None:
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Upgraded Regex to capture Indian mobile standards seamlessly."""
    pattern = r'(?:\+?91[- ]?)?[6-9]\d{9}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_skills(doc: spacy.tokens.Doc) -> list[str]:
    """Uses the globally cached PhraseMatcher to pull keywords rapidly."""
    matches = matcher(doc)
    extracted_skills = set()
    for match_id, start, end in matches:
        span = doc[start:end]
        extracted_skills.add(span.text)
    return list(extracted_skills)


def parse_resume_text(text: str) -> dict:
    """Orchestrates text parsing and returns structured candidate profiles."""
    # Normalize whitespaces
    cleaned_text = text.replace("\n", " ").replace("\r", " ")
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    # Process doc once for internal extraction layers
    doc = nlp(cleaned_text)

    return {
        "name": extract_name(text),  # Run on raw text so layout boundaries help NER
        "email": extract_email(cleaned_text),
        "phone": extract_phone(cleaned_text),
        "skills": extract_skills(doc)
    }