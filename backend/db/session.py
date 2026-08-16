from sqlalchemy import create_engine,text
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Option A: Hardcode your PostgreSQL URL for local testing
# DATABASE_URL = "postgresql://username:password@localhost:5432/your_database_name"
# Option B (Recommended): Load it dynamically from your .env file
# Fetch from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Guard clause: Fail fast if .env wasn't loaded properly
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set! Ensure load_dotenv() is called before importing session.py "
        "and that DATABASE_URL is defined in your .env file."
    )
# Clean engine creation for PostgreSQL (no check_same_thread needed)
engine = create_engine(
    DATABASE_URL,
    pool_size=50,          # Keep 50 connections open
    max_overflow=20,       # Allow up to 20 extra if needed
    pool_timeout=30.0,      # Don't crash if they have to wait
    pool_pre_ping=True     # Recommended for PG: auto-checks stale connections
)


# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that our models will inherit from
Base = declarative_base()

# Dependency tool to get a database session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()