from dotenv import load_dotenv
load_dotenv()


from sqlalchemy import text
from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from backend.db.session import engine, Base , get_db
from backend.models import models       
import time     
from fastapi import Request
from backend.routers import resume, jobs  # Clean single import for routers

app = FastAPI(
    title="AI Resume Platform API",
    description="Backend API for parsing, embedding, and ranking resumes.",
    version="1.0.0"
)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    
    # Process the actual request
    response = await call_next(request)
    
    # Calculate total duration in milliseconds
    process_time_ms = (time.perf_counter() - start_time) * 1000
    
    # Print it directly to your Uvicorn console
    print(f"🚀 Endpoint: {request.method} {request.url.path} | Latency: {process_time_ms:.2f} ms")
    
    # Optional: Attach it to the response headers
    response.headers["X-Process-Time-ms"] = str(round(process_time_ms, 2))
    return response
# --- ENABLE CORS FOR DEV ENVIRONMENT ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open to all origins for development stage
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(resume.router)
app.include_router(jobs.router)  # Included jobs routes
@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Resume Platform API. Head over to /docs for interactive endpoints."}



@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Executes a light ping to PostgreSQL
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "vector_store": "chroma_ready"
    }