import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.pdf_parser import extract_text_from_pdf
from nlp.extractor import parse_resume_text

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/resumes",
    tags=["resumes"]
)

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now!")
    
    logger.info(f"Received file upload request: {file.filename}")
    
    # 1. Use isolated service to parse PDF contents
    raw_text = extract_text_from_pdf(file.file)
    
    # 2. Extract entities via NLP
    parsed_profile = parse_resume_text(raw_text)
    
    # 3. Formulate clean telemetry payload
    return {
        "filename": file.filename,
        "status": "processed",
        "text_length": len(raw_text),
        "parsed_data": parsed_profile
    }