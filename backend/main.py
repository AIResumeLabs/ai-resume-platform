from fastapi import FastAPI
from backend.routers import resume  # Import your new router file

app = FastAPI(
    title="AI Resume Platform API",
    description="Backend API for parsing, embedding, and ranking resumes.",
    version="1.0.0"
)

# Include the resume router
app.include_router(resume.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Resume Platform API. Head over to /docs for the API documentation."}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "not_connected_yet",
        "vector_store": "not_connected_yet"
    }