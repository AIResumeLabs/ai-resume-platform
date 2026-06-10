import logging
from sqlalchemy.orm import Session
from backend.models.models import JobDescription

logger = logging.getLogger(__name__)

def create_job_description(db: Session, title: str, raw_text: str) -> JobDescription:
    """Inserts a new target Job Description role into the schema."""
    try:
        new_job = JobDescription(
            title=title,
            raw_text=raw_text
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        logger.info(f"Successfully saved new Job Description: {title} (ID: {new_job.id})")
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