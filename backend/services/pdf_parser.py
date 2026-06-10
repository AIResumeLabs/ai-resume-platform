import pdfplumber
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_object) -> str:
    """Streams and extracts raw text string contents out of a PDF file stream."""
    extracted_text = ""
    try:
        with pdfplumber.open(file_object) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        
        if not extracted_text.strip():
            raise HTTPException(
                status_code=422, 
                detail="PDF uploaded successfully, but no readable text could be extracted."
            )
            
        return extracted_text.strip()

    except pdfplumber.pdf.PDFSyntaxError:
        logger.error("Failed to parse file due to an invalid or corrupt PDF syntax.")
        raise HTTPException(status_code=400, detail="The uploaded file is corrupt or not a valid PDF syntax layout.")
    except Exception as e:
        logger.error(f"Unexpected error inside pdf_parser service: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while reading the file structure.")