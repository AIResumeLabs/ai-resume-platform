import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.models.models import JobDescription, Candidate
from nlp.embedder import embedder_instance
from vector_store.chroma_client import vector_db
from nlp.extractor import parse_resume_text  # Re-using your NLP extractor for jobs!

logger = logging.getLogger(__name__)

# --- ADJACENT DOMAIN KNOWLEDGE BASE ---
ADJACENT_TRACKS = {
    "DevOps": ["docker", "kubernetes", "aws", "cicd", "linux", "jenkins"],
    "Frontend": ["react", "typescript", "tailwind", "next.js", "javascript"],
    "Data Science": ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "sql"],
    "System Design": ["system design", "microservices", "caching", "redis", "kafka"]
}

def calculate_versatility_score(candidate_skills: list[str], secondary_domains: dict[str, list[str]]) -> dict:
    """Evaluates candidate readiness across adjacent technical tracks."""
    domain_scores = {}
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    
    for domain, skills in secondary_domains.items():
        skills_lower = [s.lower() for s in skills]
        matches = len(set(candidate_skills_lower).intersection(set(skills_lower)))
        domain_scores[domain] = matches / len(skills) if skills else 0.0
        
    overall_versatility = sum(domain_scores.values()) / len(domain_scores) if domain_scores else 0.0
    
    return {
        "overall_versatility_score": round(overall_versatility, 2),
        "domain_breakdown": domain_scores
    }

def rank_candidate_advanced(
    resume_skills: list[str],
    required_skills: list[str],
    similarity_score: float,
    adjacent_tracks: dict[str, list[str]]
) -> dict:
    
    # 1. Core Technical Fit (FIXED)
    core_set = set([s.lower() for s in required_skills])
    candidate_set = set([s.lower() for s in resume_skills])
    
    # FIX: If the job description has no tech skills (e.g. "gamer"), 
    # do NOT give them a perfect score. Give them a 0.0 for technical fit.
    core_match = len(candidate_set.intersection(core_set)) / len(core_set) if core_set else 0.0
    
    # 2. Cross-Functional Versatility
    versatility_data = calculate_versatility_score(resume_skills, adjacent_tracks)
    versatility_score = versatility_data["overall_versatility_score"]
    
    # 3. Experience Match (FIXED)
    # Defaulting to 0.0 instead of 1.0 so we don't give away free points.
    exp_score = 0.0 
    
    # 4. Composite Scoring Matrix
    final_score = (
        core_match * 0.35 +
        similarity_score * 0.40 +
        exp_score * 0.10 +
        versatility_score * 0.15
    )
    
    # ... (Keep the rest of the insight generation below exactly the same) ...
    # Generate insights
    explanation_points = []
    if versatility_score > 0.3: # Lowered threshold slightly for more dynamic insights
        top_adjacent = max(versatility_data["domain_breakdown"], key=versatility_data["domain_breakdown"].get)
        if versatility_data["domain_breakdown"][top_adjacent] > 0:
            explanation_points.append(f"Highly versatile candidate with strong secondary potential in {top_adjacent}.")
    else:
        explanation_points.append("Highly specialized profile with a tight focus on core competencies.")
        
    return {
        "final_score": round(final_score, 3),
        "breakdown": {
            "core_technical": round(core_match, 2),
            "semantic_affinity": round(similarity_score, 2),
            "cross_functional_utility": versatility_score
        },
        "insight_summary": " ".join(explanation_points)
    }

def rank_candidates_for_job(db: Session, job_id: int, top_k: int = 5):
    """
    The orchestrator: Fetches the job, extracts required skills, queries ChromaDB, 
    and applies the advanced composite ranking algorithm.
    """
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    logger.info(f"Analyzing Job: {job.title}")
    
    # 1. Parse the Job Description to find explicit required skills
    parsed_job = parse_resume_text(job.raw_text)
    required_skills = parsed_job.get("skills", [])
    
    # 2. Get the Semantic Vector matches from ChromaDB
    job_vector = embedder_instance.embed_text(job.raw_text)
    chroma_results = vector_db.search_resumes(query_vector=job_vector, top_k=top_k)

    if not chroma_results:
        return []

    ranked_candidates = []
    for match in chroma_results:
        candidate_record = db.query(Candidate).filter(Candidate.id == match["candidate_id"]).first()
        
        if candidate_record:
            candidate_skills = [s.skill_name for s in candidate_record.skills]
            semantic_score = match["score"]
            
            # 3. Apply your advanced composite ranking formula
            advanced_metrics = rank_candidate_advanced(
                resume_skills=candidate_skills,
                required_skills=required_skills,
                similarity_score=semantic_score,
                adjacent_tracks=ADJACENT_TRACKS
            )

            # Convert final score to percentage
            percentage_score = round(advanced_metrics["final_score"] * 100, 2)

            ranked_candidates.append({
                "candidate_id": candidate_record.id,
                "name": candidate_record.name,
                "email": candidate_record.email,
                "phone": candidate_record.phone,
                "filename": candidate_record.file_path,
                "match_score": percentage_score,
                "matched_skills": candidate_skills,
                "insights": advanced_metrics["insight_summary"],
                "detailed_breakdown": advanced_metrics["breakdown"]
            })

    # Sort the final list by the new composite score
    ranked_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    
    return ranked_candidates