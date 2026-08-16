import logging
import chromadb

logger = logging.getLogger(__name__)


class ResumeVectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        logger.info(f"Initializing ChromaDB at {persist_directory}...")
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="candidate_resumes",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB collection 'candidate_resumes' is ready.")

    def add_resume(self, candidate_id: int, vector: list[float], metadata: dict):
        """
        Saves (or overwrites) a candidate's vector.
        Uses upsert so re-processing a candidate (resume re-upload, re-embedding
        after a parser fix) overwrites cleanly instead of erroring on duplicate ID.
        """
        if not vector or len(vector) == 0:
            logger.error(f"Cannot save empty vector for candidate {candidate_id}")
            return False

        str_id = str(candidate_id)
        try:
            self.collection.upsert(
                ids=[str_id],
                embeddings=[vector],
                metadatas=[metadata]
            )
            logger.info(f"Vector upserted to ChromaDB for candidate_id: {str_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vector for candidate {candidate_id}: {e}")
            return False

    def add_resumes_batch(self, candidate_ids: list[int], vectors: list[list[float]], metadatas: list[dict]):
        """Batch upsert — use for bulk ingestion/backfills instead of looping add_resume."""
        if not (len(candidate_ids) == len(vectors) == len(metadatas)):
            logger.error("Batch add failed: candidate_ids, vectors, and metadatas must be same length")
            return False

        valid = [(cid, v, m) for cid, v, m in zip(candidate_ids, vectors, metadatas) if v and len(v) > 0]
        if not valid:
            logger.error("Batch add failed: no valid (non-empty) vectors provided")
            return False
        if len(valid) < len(candidate_ids):
            logger.warning(f"Skipped {len(candidate_ids) - len(valid)} candidates with empty vectors in batch")

        str_ids = [str(cid) for cid, _, _ in valid]
        try:
            self.collection.upsert(
                ids=str_ids,
                embeddings=[v for _, v, _ in valid],
                metadatas=[m for _, _, m in valid]
            )
            logger.info(f"Batch upserted {len(str_ids)} vectors to ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            return False

    def delete_resume(self, candidate_id: int):
        """
        Removes a candidate's vector. Call this whenever a candidate record
        is deleted from Postgres, or their resume is re-embedded under a
        replaced flow — otherwise stale vectors keep surfacing in search
        results (and quietly eat a slot in every ranking pool) forever.
        """
        str_id = str(candidate_id)
        try:
            self.collection.delete(ids=[str_id])
            logger.info(f"Vector deleted from ChromaDB for candidate_id: {str_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector for candidate {candidate_id}: {e}")
            return False

    def search_resumes(self, query_vector: list[float], top_k: int = 5):
        """
        Finds the top matching resumes for a given Job Description vector.
        Returns similarity scores in [0, 1], higher = better match.
        """
        if not query_vector or len(query_vector) == 0:
            logger.error("Cannot search with an empty query vector")
            return []

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []

        matches = []
        if results and results.get('ids') and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                raw_id = results['ids'][0][i]
                try:
                    candidate_id = int(raw_id)
                except (TypeError, ValueError):
                    logger.warning(f"Skipping non-numeric candidate id in search results: {raw_id}")
                    continue

                # Cosine distance -> similarity: similarity = 1 - distance
                raw_distance = results['distances'][0][i]
                similarity_score = max(0.0, min(1.0, 1.0 - raw_distance))

                matches.append({
                    "candidate_id": candidate_id,
                    "score": round(similarity_score, 4),
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                })

        return matches


vector_db = ResumeVectorStore()