import logging
import chromadb

# Initialize logger
logger = logging.getLogger(__name__)

class ResumeVectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initializes the ChromaDB client. It creates a local folder in your project
        to save vectors permanently so they survive server restarts.
        """
        logger.info(f"Initializing ChromaDB at {persist_directory}...")
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # We use Cosine Similarity because it measures the *angle* between two vectors,
        # which is the mathematical standard for comparing text documents.
        self.collection = self.client.get_or_create_collection(
            name="candidate_resumes",
            metadata={"hnsw:space": "cosine"} 
        )
        logger.info("ChromaDB collection 'candidate_resumes' is ready.")

    def add_resume(self, candidate_id: int, vector: list[float], metadata: dict):
        """
        Saves a single candidate's vector into the database.
        We link the vector directly to the SQLite candidate_id.
        """
        if not vector or len(vector) == 0:
            logger.error(f"Cannot save empty vector for candidate {candidate_id}")
            return

        # ChromaDB strictly requires IDs to be strings
        str_id = str(candidate_id)
        
        self.collection.add(
            ids=[str_id],
            embeddings=[vector],
            metadatas=[metadata]
        )
        logger.info(f"Vector saved to ChromaDB for candidate_id: {str_id}")

    def search_resumes(self, query_vector: list[float], top_k: int = 5):
        """
        Finds the top matching resumes for a given Job Description vector.
        """
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        
        matches = []
        # Safety check to ensure we actually got results back
        if results and results.get('ids') and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                # ChromaDB returns 'distance'. We convert it to a 0-1 'similarity score'.
                # For cosine, distance is 1 - similarity. So similarity is 1 - distance.
                raw_distance = results['distances'][0][i]
                similarity_score = max(0.0, 1.0 - raw_distance) 
                
                matches.append({
                    "candidate_id": int(results['ids'][0][i]),
                    "score": round(similarity_score, 4),
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                })
        
        return matches

# Create a single global instance for the backend to import
vector_db = ResumeVectorStore()
