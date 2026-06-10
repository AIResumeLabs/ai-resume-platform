from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Local SQLite database file URL
DATABASE_URL = "sqlite:///./resume_platform.db"

# Create the engine instance
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed only for SQLite
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