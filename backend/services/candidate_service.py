import logging
from sqlalchemy.orm import Session
from backend.models.models import Candidate, CandidateSkill

logger = logging.getLogger(__name__)

def save_parsed_candidate(db: Session, parsed_data: dict, raw_text: str, filename: str) -> Candidate:
    try:
        new_candidate = Candidate(
            name=parsed_data.get("name"),
            email=parsed_data.get("email"),
            phone=parsed_data.get("phone"),
            raw_text=raw_text,
            file_path=filename,
            parsed_profile=parsed_data  # <--- SAVE THE RICH JSON HERE
        )
        
        db.add(new_candidate)
        db.flush() 
        
        skills_to_insert = []
        # Update the loop to handle the new dictionary structure
        for skill_dict in parsed_data.get("skills", []):
            skill_record = CandidateSkill(
                candidate_id=new_candidate.id,
                skill_name=skill_dict.get("skill_name", "Unknown")
            )
            skills_to_insert.append(skill_record)
        
        if skills_to_insert:
            db.add_all(skills_to_insert)
            
        db.commit()
        db.refresh(new_candidate)
        return new_candidate

    except Exception as e:
        db.rollback() 
        raise e

def get_all_candidates(db: Session):
    """Fetches all candidate records from the database."""
    return db.query(Candidate).all()

def get_candidate_by_id(db: Session, candidate_id: int):
    """Fetches a specific candidate by their unique primary key ID."""
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()