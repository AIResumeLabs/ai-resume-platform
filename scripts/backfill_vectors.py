import sys
import os

# This tells Python to look at the root folder so we can import backend and nlp modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.session import SessionLocal
from backend.models.models import Candidate
from nlp.embedder import embedder_instance
from vector_store.chroma_client import vector_db

def run_backfill():
    print("Connecting to SQLite database...")
    db = SessionLocal()
    
    # Grab every single candidate currently sitting in SQLite
    candidates = db.query(Candidate).all()
    print(f"Found {len(candidates)} existing candidates in SQLite.")
    
    if not candidates:
        print("Database is empty. Nothing to sync!")
        return

    for candidate in candidates:
        print(f"\nProcessing ID {candidate.id}: {candidate.name}...")
        
        # 1. Reconstruct the skills dictionary that the embedder expects
        skills_list = [skill.skill_name for skill in candidate.skills]
        parsed_profile = {"skills": skills_list}
        
        # 2. Generate the math vector
        vector = embedder_instance.embed_candidate(parsed_profile)
        
        # 3. Save it to ChromaDB
        vector_db.add_resume(
            candidate_id=candidate.id,
            vector=vector,
            metadata={
                "name": candidate.name or "Unknown",
                "email": candidate.email or "Unknown"
            }
        )
        print(f"  -> Successfully synced candidate {candidate.id} to ChromaDB.")
        
    db.close()
    print("\nBackfill complete! SQLite and ChromaDB are now completely in sync.")

if __name__ == "__main__":
    run_backfill()