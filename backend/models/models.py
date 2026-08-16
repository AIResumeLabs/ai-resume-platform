from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime,JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.db.session import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    # --- NEW COLUMN: Stores the rich skill data with 1-5 proficiency scores ---
    parsed_profile = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="candidate")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    skill_name = Column(String, index=True, nullable=False)

    # Relationship back to parent
    candidate = relationship("Candidate", back_populates="skills")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    raw_text = Column(Text, nullable=False)
    # --- NEW COLUMN: Saves the Gemini extraction permanently ---
    parsed_skills = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    rankings = relationship("Ranking", back_populates="job")


class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    score = Column(Float, nullable=False)
    breakdown = Column(JSONB, nullable=True)  # Upgraded to native PostgreSQL JSONB!
    ranked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="rankings")
    job = relationship("JobDescription", back_populates="rankings")