from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db.session import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    rankings = relationship("Ranking", back_populates="job")


class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    score = Column(Float, nullable=False)
    breakdown = Column(Text, nullable=True)  # Will store score JSON as a string split
    ranked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    candidate = relationship("Candidate", back_populates="rankings")
    job = relationship("JobDescription", back_populates="rankings")