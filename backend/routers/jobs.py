import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services import job_service
from backend.services.ranking_service import rank_candidates_for_job

# Import Pydantic Schemas
from backend.schemas.schemas import (
    JobCreateRequest,
    JobCreateResponse,
    JobListResponse,
    JobDetailResponse,
    JobMatchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"]
)


@router.post("/", response_model=JobCreateResponse, status_code=201)
async def create_job(payload: JobCreateRequest, db: Session = Depends(get_db)):
    logger.info(f"Received request to create job profile: {payload.title}")
    if not payload.title.strip() or not payload.raw_text.strip():
        raise HTTPException(
            status_code=400, 
            detail="Title and raw_text fields cannot be empty strings."
        )
        
    job = job_service.create_job_description(db, title=payload.title, raw_text=payload.raw_text)
    return {
        "job_id": job.id,
        "title": job.title,
        "status": "created_successfully",
        "created_at": job.created_at
    }


@router.get("/", response_model=List[JobListResponse])
async def list_jobs(db: Session = Depends(get_db)):
    jobs = job_service.get_all_jobs(db)
    return [{
        "id": j.id,
        "title": j.title,
        "text_length": len(j.raw_text),
        "created_at": j.created_at
    } for j in jobs]


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    job = job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=404, 
            detail=f"Job opportunity with ID {job_id} was not found."
        )
    return {
        "job_id": job.id,
        "title": job.title,
        "raw_text": job.raw_text,
        "created_at": job.created_at
    }


@router.get("/{job_id}/match", response_model=JobMatchResponse)
async def match_candidates_for_job(job_id: int, top_k: int = 5, db: Session = Depends(get_db)):
    """
    Triggers the AI matchmaking engine. 
    Takes a Job ID, embeds its description, searches ChromaDB, 
    and returns the top 'k' most relevant candidates with their percentage scores.
    """
    logger.info(f"Initiating AI matchmaking for Job ID: {job_id}")
    
    try:
        ranked_results = await run_in_threadpool(
            rank_candidates_for_job, 
            db=db, 
            job_id=job_id, 
            top_k=top_k
        )
        
        if not ranked_results:
            return {
                "job_id": job_id,
                "status": "success",
                "total_matches_returned": 0,
                "message": "No relevant candidates found in the database.",
                "matches": []
            }
            
        return {
            "job_id": job_id,
            "status": "success",
            "total_matches_returned": len(ranked_results),
            "matches": ranked_results
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Matchmaking failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An error occurred during the AI ranking process."
        )