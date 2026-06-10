import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.db.session import get_db
from backend.services import job_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"]
)

# Simple input schema validation for creating jobs
class JobCreateRequest(BaseModel):
    title: str
    raw_text: str

@router.post("/")
async def create_job(payload: JobCreateRequest, db: Session = Depends(get_db)):
    logger.info(f"Received request to create job profile: {payload.title}")
    if not payload.title.strip() or not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Title and raw_text fields cannot be empty strings.")
        
    job = job_service.create_job_description(db, title=payload.title, raw_text=payload.raw_text)
    return {
        "job_id": job.id,
        "title": job.title,
        "status": "created_successfully",
        "created_at": job.created_at
    }

@router.get("/")
async def list_jobs(db: Session = Depends(get_db)):
    jobs = job_service.get_all_jobs(db)
    return [{
        "id": j.id,
        "title": j.title,
        "text_length": len(j.raw_text),
        "created_at": j.created_at
    } for j in jobs]

@router.get("/{job_id}")
async def get_job(job_id: int, db: Session = Depends(get_db)):
    job = job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job opportunity with ID {job_id} was not found.")
    return {
        "job_id": job.id,
        "title": job.title,
        "raw_text": job.raw_text,
        "created_at": job.created_at
    }