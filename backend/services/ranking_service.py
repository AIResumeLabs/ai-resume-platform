import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.models.models import JobDescription, Candidate
from nlp.embedder import embedder_instance
from vector_store.chroma_client import vector_db
from nlp.extractor import parse_resume_text 

logger = logging.getLogger(__name__)

# ==============================================================================
# ADVANCED QUANT/CORE ENGINEERING FILTERING SYSTEM
# ==============================================================================

QUANT_CRITICAL_SKILLS = {
    "c++", "probability", "statistics", "algorithms", "data structures",
    "quantitative finance", "stochastic processes", "competitive programming",
    "time series analysis", "machine learning"
}

def rank_candidate_advanced(
    resume_skills: list[str],
    required_skills: list[str],
    raw_similarity_score: float
) -> dict:
    
    # CRASH FIX: Strip out any accidental 'None' values the LLM might have returned
    safe_req = [s for s in required_skills if s is not None]
    safe_res = [s for s in resume_skills if s is not None]
    
    core_set = set([s.lower() for s in safe_req])
    candidate_set = set([s.lower() for s in safe_res])
    
    # 1. TIERED SKILL MATCHING
    total_possible = 0.0
    earned = 0.0
    critical_hits = 0
    
    for skill in core_set:
        weight = 3.0 if skill in QUANT_CRITICAL_SKILLS else 1.0
        total_possible += weight
        
        if skill in candidate_set:
            earned += weight
            if skill in QUANT_CRITICAL_SKILLS:
                critical_hits += 1
                
    core_match = (earned / total_possible) if total_possible > 0 else 0.0
    
    # 2. STRICT SEMANTIC SCALING
    adjusted_similarity = max(0.0, (raw_similarity_score - 0.45) / 0.55)
    
    # 3. BASELINE SCORE
    base_score = (adjusted_similarity * 0.35) + (core_match * 0.65)
    
    # 4. THE KNOCKOUT PENALTY
    jd_has_critical = len(core_set.intersection(QUANT_CRITICAL_SKILLS)) > 0
    
    if jd_has_critical and critical_hits == 0:
        final_score = base_score * 0.40
        insight = "⚠️ GATEKEEPER FILTER: Candidate severely lacks required critical quantitative or core engineering fundamentals."
    elif jd_has_critical and critical_hits >= 2:
        final_score = min(1.0, base_score * 1.15)
        insight = "⭐ PREMIUM MATCH: Candidate demonstrates strong overlap with critical quantitative fundamentals."
    else:
        final_score = base_score
        insight = "Standard match based on general technical alignment and vector similarity."

    return {
        "final_score": round(final_score, 3),
        "breakdown": {
            "weighted_skill_match": round(core_match, 2),
            "adjusted_semantic_affinity": round(adjusted_similarity, 2),
            "critical_hits": critical_hits
        },
        "insight_summary": insight
    }

def rank_candidates_for_job(db: Session, job_id: int, top_k: int = 5):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    logger.info(f"Analyzing Job: {job.title}")
    
    # CRASH FIX: Prevent 'NoneType' crashes by falling back to empty strings
    safe_title = job.title if job.title else "Unknown Role"
    safe_raw_text = job.raw_text if job.raw_text else ""
    
    # Combine title and text so the LLM gets the full context
    combined_job_text = f"Job Title: {safe_title}\nRequirements: {safe_raw_text}"
    
    # 1. Parse using Gemini
    parsed_job = parse_resume_text(combined_job_text)
    required_skills = parsed_job.get("skills") or []  # 'or []' protects against None
    
    # 2. Symmetric Embedding Logic
    if required_skills:
        job_text_to_embed = f"Job Title: {safe_title}. Candidate skilled in: " + ", ".join(required_skills)
    else:
        job_text_to_embed = combined_job_text
        
    job_vector = embedder_instance.embed_text(job_text_to_embed)
    chroma_results = vector_db.search_resumes(query_vector=job_vector, top_k=top_k)

    if not chroma_results:
        return []

    ranked_candidates = []
    for match in chroma_results:
        candidate_record = db.query(Candidate).filter(Candidate.id == match["candidate_id"]).first()
        
        if candidate_record:
            candidate_skills = [s.skill_name for s in candidate_record.skills]
            semantic_score = match["score"]
            
            advanced_metrics = rank_candidate_advanced(
                resume_skills=candidate_skills,
                required_skills=required_skills,
                raw_similarity_score=semantic_score
            )

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
            
    ranked_candidates.sort(key=lambda x: x["match_score"], reverse=True)  
    return ranked_candidates