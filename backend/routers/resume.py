import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.pdf_parser import extract_text_from_pdf
from nlp.extractor import parse_resume_text
from backend.services.candidate_service import save_parsed_candidate  # Import the new DB service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/resumes",
    tags=["resumes"]
)

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now!")
    
    logger.info(f"Processing uploaded file: {file.filename}")
    
    # 1. Parse text out of incoming file object stream
    raw_text = extract_text_from_pdf(file.file)
    
    # 2. Parse structural entities via spaCy NLP
    parsed_profile = parse_resume_text(raw_text)
    
    # 3. --- PERSIST AND SAVE RESULTS TO SQLITE ---
    db_candidate = save_parsed_candidate(
        db=db, 
        parsed_data=parsed_profile, 
        raw_text=raw_text, 
        filename=file.filename
    )
    
    return {
        "candidate_id": db_candidate.id,
        "filename": db_candidate.file_path,
        "status": "successfully_saved_to_db",
        "text_length": len(raw_text),
        "parsed_data": {
            "name": db_candidate.name,
            "email": db_candidate.email,
            "phone": db_candidate.phone,
            "skills": [s.skill_name for s in db_candidate.skills]
        }
    }