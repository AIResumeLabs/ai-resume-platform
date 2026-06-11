import logging
from sentence_transformers import SentenceTransformer

# Initialize logger
logger = logging.getLogger(__name__)

class VectorEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initializes the embedding model. This is wrapped in a class so it 
        happens exactly ONCE when the server starts, preventing memory crashes.
        """
        logger.info(f"Loading embedding model: {model_name}. This may take a moment...")
        # Downloads the model on first run, loads from local cache after that
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully.")

    def embed_text(self, text: str) -> list[float]:
        """
        Core method to convert any raw text string into a 384-dimensional vector.
        Used primarily for Job Descriptions.
        """
        if not text or not text.strip():
            logger.warning("Empty text passed to embedder.")
            # Return an array of 384 zeros if text is missing, so ChromaDB doesn't crash
            return [0.0] * 384 
        
        # .encode() returns a NumPy array. ChromaDB strictly requires standard Python lists.
        return self.model.encode(text).tolist()

    def embed_candidate(self, parsed_data: dict) -> list[float]:
        """
        Takes the exact dictionary output from the NLP extractor, flattens 
        the relevant parts into a single string, and embeds it.
        """
        # CRITICAL: We DO NOT embed names, emails, or phone numbers. 
        # A name like "Vaibhav" has no semantic mathematical relationship to a Job Description.
        skills = parsed_data.get("skills", [])
        
        if not skills:
            logger.warning("No skills found in parsed candidate data to embed.")
            text_to_embed = "No technical skills extracted."
        else:
            # Flatten array: ["Python", "FastAPI"] -> "Candidate skilled in: Python, FastAPI"
            text_to_embed = "Candidate skilled in: " + ", ".join(skills)
            
        return self.embed_text(text_to_embed)

# Create a single global instance. 
# Your backend friend will import THIS exact variable into the router.
embedder_instance = VectorEmbedder()
