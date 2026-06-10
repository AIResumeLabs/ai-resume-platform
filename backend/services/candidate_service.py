import logging
from sqlalchemy.orm import Session
from backend.models.models import Candidate, CandidateSkill

logger = logging.getLogger(__name__)

def save_parsed_candidate(db: Session, parsed_data: dict, raw_text: str, filename: str) -> Candidate:
    """
    Takes parsed NLP dictionary data, initiates a database transaction,
    saves the Candidate object, maps and saves their Skills array, and commits.
    """
    try:
        # 1. Create the base Candidate record
        new_candidate = Candidate(
            name=parsed_data.get("name"),
            email=parsed_data.get("email"),
            phone=parsed_data.get("phone"),
            raw_text=raw_text,
            file_path=filename  # Saving filename as local reference tracker
        )
        
        db.add(new_candidate)
        db.flush()  # Flush pushes the candidate to DB to generate 'new_candidate.id' before committing
        
        # 2. Iterate through extracted skills array and link them to this candidate ID
        skills_to_insert = []
        for skill in parsed_data.get("skills", []):
            skill_record = CandidateSkill(
                candidate_id=new_candidate.id,
                skill_name=skill
            )
            skills_to_insert.append(skill_record)
        
        if skills_to_insert:
            db.add_all(skills_to_insert)
            
        # 3. Commit everything cleanly to the database file
        db.commit()
        db.refresh(new_candidate)
        
        logger.info(f"Successfully saved candidate {new_candidate.name or filename} to DB with ID {new_candidate.id}")
        return new_candidate

    except Exception as e:
        db.rollback()  # Rollback changes if anything crashes to avoid partial database data corruptions
        logger.error(f"Failed to persist candidate transaction to database: {str(e)}")
        raise e
    # Append to backend/services/candidate_service.py

def get_all_candidates(db: Session):
    """Fetches all candidate records from the database."""
    return db.query(Candidate).all()

def get_candidate_by_id(db: Session, candidate_id: int):
    """Fetches a specific candidate by their unique primary key ID."""
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()