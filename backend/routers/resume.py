from fastapi import APIRouter, UploadFile, File, HTTPException
import pdfplumber

router = APIRouter(
    prefix="/api/resumes",
    tags=["resumes"]
)

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    # 1. Validate that it's a PDF
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now!")
    
    try:
        # 2. Open the PDF file stream using pdfplumber
        extracted_text = ""
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        
        # 3. Quick guard check to see if we actually got text out of it
        if not extracted_text.strip():
            raise HTTPException(status_code=422, detail="PDF uploaded successfully, but no readable text could be extracted.")

        # 4. Return the response
        return {
            "filename": file.filename,
            "status": "processed",
            "extracted_text": extracted_text.strip()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while parsing the PDF: {str(e)}")