import logging
import json
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.models.models import JobDescription, Candidate, Ranking
from nlp.embedder import embedder_instance
from vector_store.chroma_client import vector_db
import time
logger = logging.getLogger(__name__)

# ==============================================================================
# DYNAMIC LLM-WEIGHTED RANKING SYSTEM
# ==============================================================================

SKILL_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "k8s": "kubernetes",
    "cpp": "c++",
    "csharp": "c#",
    "postgres": "postgresql",
    "problemsolving": "problem solving"
}

# --- NEW: HIERARCHICAL SKILL CATEGORIES ---
# Maps broad JD requirements to specific candidate skills
SKILL_CATEGORIES = {
    "sql": ["sql", "mysql", "postgresql", "sqlite", "oracle", "sql server"],
    "orm": ["orm", "sqlalchemy", "hibernate", "prisma", "django orm"],
    "problem solving": ["problem solving", "competitive programming", "algorithms", "data structures"],
    "rest api": ["rest api", "fastapi", "flask", "django", "express", "api"],
    "version control": ["version control", "git", "github", "gitlab", "bitbucket"],
    "aws": ["aws", "amazon web services", "ec2", "s3"],
    "authentication": ["authentication", "jwt", "oauth", "auth", "security"]
}

def normalize_skill(name: str) -> str:
    name = (name or "").lower().strip()
    name = re.sub(r"[^a-z0-9+#. ]", "", name)
    return SKILL_ALIASES.get(name, name)

def skills_match(jd_skill: str, cand_skill: str) -> bool:
    """Matches exact strings, partial word boundaries, and hierarchical categories."""
    if not jd_skill or not cand_skill:
        return False
        
    jd_skill = jd_skill.strip()
    cand_skill = cand_skill.strip()
    
    if jd_skill == cand_skill:
        return True

    # 1. CATEGORY MATCHING (e.g., JD asks for "orm", candidate has "sqlalchemy")
    for category, members in SKILL_CATEGORIES.items():
        if jd_skill == category and cand_skill in members:
            return True
        # Reverse check: JD asks for "sqlalchemy", candidate just wrote "orm"
        if cand_skill == category and jd_skill in members:
            return True

    # 2. SUBSTRING MATCHING (e.g., JD asks for "postgres", candidate has "postgresql")
    if jd_skill in cand_skill or cand_skill in jd_skill:
        return True

    # 3. REGEX WORD BOUNDARY MATCHING
    pattern_a = r"(?<![\w+#]){}(?![\w+#])".format(re.escape(jd_skill))
    pattern_b = r"(?<![\w+#]){}(?![\w+#])".format(re.escape(cand_skill))
    return bool(re.search(pattern_a, cand_skill) or re.search(pattern_b, jd_skill))


def safe_float(val, default: float) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def rank_candidate_dynamic(
    rich_candidate_skills: list[dict],
    weighted_jd_skills: list[dict],
    raw_similarity_score: float,
    critical_hit_threshold: float = 3.0,
) -> dict:
    rich_candidate_skills = rich_candidate_skills or []
    weighted_jd_skills = weighted_jd_skills or []

    cand_dict: dict[str, dict] = {}
    for s in rich_candidate_skills:
        if not isinstance(s, dict):
            continue
        name = normalize_skill(s.get("skill_name", ""))
        if not name:
            continue
        prof = safe_float(s.get("proficiency_score"), 1.0)
        if name not in cand_dict or prof > cand_dict[name]["proficiency_score"]:
            cand_dict[name] = {
                "proficiency_score": prof,
                "evidence": s.get("evidence", ""),
                "display_name": s.get("skill_name", name),
            }

    seen_jd_skills: dict[str, float] = {}
    for req in weighted_jd_skills:
        if not isinstance(req, dict):
            continue
        jd_skill = normalize_skill(req.get("skill", ""))
        jd_weight = safe_float(req.get("weight"), 1.0)
        if not jd_skill:
            continue
        if jd_skill not in seen_jd_skills or jd_weight > seen_jd_skills[jd_skill]:
            seen_jd_skills[jd_skill] = jd_weight

    total_possible_points = 0.0
    earned_points = 0.0
    critical_skills_required = 0
    critical_skills_hit = 0
    critical_hit_ratio_sum = 0.0
    matched_skills = []  

    for jd_skill, jd_weight in seen_jd_skills.items():
        # FIX 1: Set the baseline expectation to 3.0 (Intermediate) instead of 5.0
        total_possible_points += (jd_weight * 3.0)
        is_critical = jd_weight >= 4.0
        if is_critical:
            critical_skills_required += 1

        best_prof_score = 0.0
        best_match_name = None
        for c_skill_name, c_skill_data in cand_dict.items():
            if skills_match(jd_skill, c_skill_name):
                if c_skill_data["proficiency_score"] > best_prof_score:
                    best_prof_score = c_skill_data["proficiency_score"]
                    best_match_name = c_skill_data["display_name"]

        if best_prof_score > 0:
            earned_points += (jd_weight * best_prof_score)
            matched_skills.append({
                "jd_skill": jd_skill,
                "candidate_skill": best_match_name,
                "proficiency": best_prof_score,
                "jd_weight": jd_weight,
                "critical": is_critical,
            })
            if is_critical:
                hit_ratio = min(1.0, best_prof_score / critical_hit_threshold)
                critical_hit_ratio_sum += hit_ratio
                if best_prof_score >= critical_hit_threshold:
                    critical_skills_hit += 1
        else:
            # FIX 2: Expose missing skills so the frontend can display them!
            matched_skills.append({
                "jd_skill": jd_skill,
                "candidate_skill": "MISSING",
                "proficiency": 0.0,
                "jd_weight": jd_weight,
                "critical": is_critical,
            })

    # FIX 3: Cap core match at 1.0 (100%)
    core_match = min(1.0, (earned_points / total_possible_points)) if total_possible_points > 0 else 0.0
    
    # Soften the semantic scaling so vectors don't unfairly drag down good skill matches
    adjusted_similarity = max(0.0, min(1.0, safe_float(raw_similarity_score, 0.0)))
    base_score = (adjusted_similarity * 0.20) + (core_match * 0.80)

    if critical_skills_required > 0:
        avg_critical_ratio = critical_hit_ratio_sum / critical_skills_required
        multiplier = 0.70 + (avg_critical_ratio * 0.40)
        final_score = min(1.0, base_score * multiplier)

        if avg_critical_ratio == 0.0:
            insight = "⚠️ Missing required experience depth. Candidate lists skills, but lacks proven project impact in critical areas."
        elif critical_skills_hit >= (critical_skills_required * 0.75):
            insight = "⭐ HIGH IMPACT: Candidate demonstrates proven, deep project experience with the most critical requirements."
        elif avg_critical_ratio < 0.5:
            insight = "⚠️ Partial critical coverage. Candidate has some exposure to critical skills but limited depth."
        else:
            insight = "Standard match. Combination of semantic alignment and moderate project experience."
    else:
        final_score = base_score
        insight = "Standard match. Combination of semantic alignment and moderate project experience."

    return {
        "final_score": round(final_score, 3),
        "breakdown": {
            "impact_weighted_match": round(core_match, 2),
            "vector_affinity": round(adjusted_similarity, 2),
            "critical_skill_ratio": round(
                (critical_hit_ratio_sum / critical_skills_required) if critical_skills_required > 0 else 1.0, 2
            ),
        },
        "matched_skills": matched_skills, 
        "insight_summary": insight,
    }


def rank_candidates_for_job(db: Session, job_id: int, top_k: int = 5, candidate_pool_multiplier: int = 5):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    logger.info(f"Analyzing Job: {job.title} (id={job_id})")

    weighted_jd_skills = job.parsed_skills or []
    if not isinstance(weighted_jd_skills, list):
        logger.warning(f"job {job_id} parsed_skills is not a list, defaulting to empty")
        weighted_jd_skills = []

    safe_title = job.title if job.title else "Unknown Role"
    safe_raw_text = job.raw_text if job.raw_text else ""
    combined_job_text = f"Job Title: {safe_title}\nRequirements: {safe_raw_text}"

    flat_required_skills = [
        item.get("skill") for item in weighted_jd_skills
        if isinstance(item, dict) and item.get("skill")
    ]

    if flat_required_skills:
        job_text_to_embed = f"Job Title: {safe_title}. Candidate skilled in: " + ", ".join(flat_required_skills)
    else:
        job_text_to_embed = combined_job_text

    job_vector = embedder_instance.embed_text(job_text_to_embed)

    # IMPORTANT: pull a much larger pool than top_k from the vector store.
    # rank_candidate_dynamic weights skill-match at 80% vs 20% vector similarity,
    # so a candidate who's semantically mediocre but skill-perfect can easily
    # outrank the pure-vector top_k — but only if they're in the pool to begin with.
    retrieval_pool_size = max(top_k * candidate_pool_multiplier, 25)
    # Start the high-precision timer
    search_start_time = time.perf_counter()
    chroma_results = vector_db.search_resumes(query_vector=job_vector, top_k=retrieval_pool_size)
    # Stop the timer and convert to milliseconds
    search_duration_ms = (time.perf_counter() - search_start_time) * 1000
    logger.info(f"⚡ ChromaDB Vector Search Time: {search_duration_ms:.2f} ms")
    if not chroma_results:
        return []

    ranked_candidates = []
    pending_rankings = []

    for match in chroma_results:
        candidate_record = db.query(Candidate).filter(Candidate.id == match["candidate_id"]).first()

        if not candidate_record:
            logger.warning(f"Candidate id={match['candidate_id']} in vector store but not found in DB, skipping")
            continue

        parsed_profile = candidate_record.parsed_profile or {}
        candidate_rich_skills = parsed_profile.get("skills", []) if isinstance(parsed_profile, dict) else []
        semantic_score = safe_float(match.get("score"), 0.0)

        try:
            advanced_metrics = rank_candidate_dynamic(candidate_rich_skills, weighted_jd_skills, semantic_score)
        except Exception as e:
            logger.error(f"Scoring failed for candidate {candidate_record.id}: {e}")
            continue

        percentage_score = round(advanced_metrics["final_score"] * 100, 2)

        pending_rankings.append((candidate_record, percentage_score, advanced_metrics))

        ranked_candidates.append({
            "candidate_id": candidate_record.id,
            "name": candidate_record.name,
            "email": candidate_record.email,
            "phone": candidate_record.phone,
            "filename": candidate_record.file_path,
            "match_score": percentage_score,
            "matched_skills": advanced_metrics["matched_skills"],  # actual matches, not the raw skill dump
            "insights": advanced_metrics["insight_summary"],
            "detailed_breakdown": advanced_metrics["breakdown"],
        })

    # Sort BEFORE truncating to top_k — this is the actual reranking step.
    ranked_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    ranked_candidates = ranked_candidates[:top_k]
    top_candidate_ids = {c["candidate_id"] for c in ranked_candidates}

    # Batch persistence — one commit instead of one per candidate.
    try:
        for candidate_record, percentage_score, advanced_metrics in pending_rankings:
            if candidate_record.id not in top_candidate_ids:
                continue  # only persist rankings for the final top_k, not the whole pool
            existing_ranking = db.query(Ranking).filter(
                Ranking.job_id == job.id,
                Ranking.candidate_id == candidate_record.id
            ).first()

            if existing_ranking:
                existing_ranking.score = percentage_score
                existing_ranking.breakdown = json.dumps(advanced_metrics["breakdown"])
            else:
                db.add(Ranking(
                    candidate_id=candidate_record.id,
                    job_id=job.id,
                    score=percentage_score,
                    breakdown=json.dumps(advanced_metrics["breakdown"]),
                ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist rankings for job {job_id}: {e}")

    return ranked_candidates