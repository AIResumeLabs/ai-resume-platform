import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.pdf_parser import extract_text_from_pdf
from nlp.extractor import parse_resume_text
from backend.services import candidate_service 
from backend.services.candidate_service import save_parsed_candidate
from nlp.embedder import embedder_instance
from vector_store.chroma_client import vector_db

# Import Pydantic Schemas
from backend.schemas.schemas import (
    ResumeUploadResponse,
    CandidateListResponse,
    CandidateDetailResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/resumes",
    tags=["resumes"]
)


@router.post("/upload", response_model=ResumeUploadResponse, status_code=201)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now!")
    
    logger.info(f"Processing uploaded file: {file.filename}")
    
    # 1. Parse text out of incoming file object stream
    raw_text = extract_text_from_pdf(file.file)
    
    # 2. Parse structural entities via spaCy NLP
    parsed_profile = parse_resume_text(raw_text)
    
    # 3. Persist to PostgreSQL
    db_candidate = save_parsed_candidate(
        db=db, 
        parsed_data=parsed_profile, 
        raw_text=raw_text, 
        filename=file.filename
    )
    
    # 4. Generate embeddings and save to ChromaDB
    try:
        resume_vector = embedder_instance.embed_candidate(parsed_profile)
        
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


@router.get("/", response_model=List[CandidateListResponse])
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


@router.get("/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate_by_id(candidate_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching candidate record for ID: {candidate_id} via service layer.")
    candidate = candidate_service.get_candidate_by_id(db, candidate_id)
    
    if not candidate:
        raise HTTPException(
            status_code=404, 
            detail=f"Candidate with ID {candidate_id} not found."
        )
        
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