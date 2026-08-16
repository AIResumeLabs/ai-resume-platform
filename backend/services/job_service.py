import logging
from sqlalchemy.orm import Session
from backend.models.models import JobDescription
from nlp.extractor import parse_job_requirements  # Import the parser here

logger = logging.getLogger(__name__)

def create_job_description(db: Session, title: str, raw_text: str) -> JobDescription:
    """Inserts a new target Job Description and extracts weighted skills via LLM."""
    
    # 1. Parse the JD using Gemini exactly ONCE here
    combined_text = f"Job Title: {title}\nRequirements: {raw_text}"
    weighted_skills = parse_job_requirements(combined_text)
    
    try:
        new_job = JobDescription(
            title=title,
            raw_text=raw_text,
            parsed_skills=weighted_skills  # 2. Save the JSON directly to PostgreSQL
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        logger.info(f"Successfully saved Job Description and cached skills: {title}")
        return new_job
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save job description: {str(e)}")
        raise e

def get_all_jobs(db: Session):
    """Retrieves all stored job opportunities."""
    return db.query(JobDescription).all()

def get_job_by_id(db: Session, job_id: int):
    """Retrieves a single specific job opportunity by ID."""
    return db.query(JobDescription).filter(JobDescription.id == job_id).first()