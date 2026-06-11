import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.models.models import Candidate
from backend.db.session import get_db
from backend.services.pdf_parser import extract_text_from_pdf
from nlp.extractor import parse_resume_text
from backend.services.candidate_service import save_parsed_candidate

# --- YOUR NEW IMPORTS ---
from nlp.embedder import embedder_instance
from vector_store.chroma_client import vector_db

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
    
    # 4. --- GENERATE EMBEDDINGS AND SAVE TO CHROMADB ---
    try:
        # Convert the parsed dictionary into a math vector
        resume_vector = embedder_instance.embed_candidate(parsed_profile)
        
        # Save it to ChromaDB, linked to the exact SQLite candidate ID
        vector_db.add_resume(
            candidate_id=db_candidate.id,
            vector=resume_vector,
            metadata={
                "name": db_candidate.name or "Unknown", 
                "email": db_candidate.email or "Unknown"
            }
        )
    except Exception as e:
        logger.error(f"Failed to save vector to ChromaDB: {str(e)}")
        # We don't raise an exception here because the SQLite save worked, 
        # but we definitely want to log it if the AI part fails.

    
    return {
        "candidate_id": db_candidate.id,
        "filename": db_candidate.file_path,
        "status": "successfully_saved_to_db_and_vector_store",
        "text_length": len(raw_text),
        "parsed_data": {
            "name": db_candidate.name,
            "email": db_candidate.email,
            "phone": db_candidate.phone,
            "skills": [s.skill_name for s in db_candidate.skills]
        }
    }

# Inside backend/routers/resumes.py - Update your GET endpoints:

from backend.services import candidate_service  # Ensure this import is present at the top

@router.get("/")
async def list_candidates(db: Session = Depends(get_db)):
    logger.info("Fetching all candidates via service layer.")
    candidates = candidate_service.get_all_candidates(db)
    
    return [{
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "filename": c.file_path,
        "uploaded_at": c.uploaded_at
    } for c in candidates]


@router.get("/{candidate_id}")
async def get_candidate_by_id(candidate_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching candidate record for ID: {candidate_id} via service layer.")
    candidate = candidate_service.get_candidate_by_id(db, candidate_id)
    
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate with ID {candidate_id} not found.")
        
    return {
        "candidate_id": candidate.id,
        "filename": candidate.file_path,
        "uploaded_at": candidate.uploaded_at,
        "parsed_data": {
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "skills": [s.skill_name for s in candidate.skills]
        }
    }