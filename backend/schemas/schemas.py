from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# CANDIDATE & RESUME SCHEMAS
# =====================================================================

class CandidateParsedData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    candidate_id: int
    filename: Optional[str] = None
    status: str
    text_length: int
    parsed_data: CandidateParsedData


class CandidateListResponse(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    filename: Optional[str] = None
    uploaded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CandidateDetailResponse(BaseModel):
    candidate_id: int
    filename: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    parsed_data: CandidateParsedData


# =====================================================================
# JOB DESCRIPTION SCHEMAS
# =====================================================================

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Job title cannot be empty.")
    raw_text: str = Field(..., min_length=1, description="Raw job description text.")


class JobCreateResponse(BaseModel):
    job_id: int
    title: str
    status: str
    created_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    id: int
    title: str
    text_length: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(BaseModel):
    job_id: int
    title: str
    raw_text: str
    created_at: Optional[datetime] = None


# =====================================================================
# MATCHMAKING & RANKING SCHEMAS
# =====================================================================

class CandidateMatchItem(BaseModel):
    candidate_id: int
    score: float
    name: Optional[str] = None
    email: Optional[str] = None
    breakdown: Optional[Dict[str, Any]] = None


class JobMatchResponse(BaseModel):
    job_id: int
    status: str = "success"
    total_matches_returned: int = 0
    message: Optional[str] = None
    matches: List[Dict[str, Any]] = Field(default_factory=list)