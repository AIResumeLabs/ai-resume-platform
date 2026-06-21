from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.session import engine, Base  
from backend.models import models            
from backend.routers import resume, jobs  # Clean single import for routers
# Generate all database tables on application startup
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="AI Resume Platform API",
    description="Backend API for parsing, embedding, and ranking resumes.",
    version="1.0.0"
)

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
def health_check():
    return {
        "status": "healthy",
        "database": "not_connected_yet",
        "vector_store": "not_connected_yet"
    }