from typing import List, Optional, Union
from openai import AzureOpenAI
from src.core.custom_logger import CustomLogger
from src.core.config import Config

class TextEmbedder:
    """
    Enterprise-level text embedder using Azure OpenAI embeddings API.
    Supports single and batch text embedding with robust logging.
    """

    def __init__(
        self,
        logger: Optional[CustomLogger] = None,
        model: Optional[str] = None
    ):
        self.logger = logger or CustomLogger("TextEmbedder")
        try:
            self.client = AzureOpenAI(
                api_version=Config.DIAL_API_VERSION or "2023-12-01-preview",
                azure_endpoint=Config.DIAL_API_ENDPOINT,
                api_key=Config.DIAL_API_KEY,
            )
            self.model = model or "text-embedding-ada-002"
            self.logger.info("AzureOpenAI embedding client initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize AzureOpenAI embedding client: {e}")
            raise

    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text string.
        Returns the embedding vector or None on failure.
        """
        try:
            self.logger.debug(f"Embedding text: {text[:50]}...")
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            embedding = response.data[0].embedding
            self.logger.info("Text embedding generated successfully.")
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for a batch of text strings.
        Returns a list of embedding vectors (or None for failed items).
        """
        embeddings = []
        for text in texts:
            embedding = self.embed_text(text)
            embeddings.append(embedding)
        return embeddings

    def embed_text_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in one API call
        """
        try:
            if not texts:
                return []
                
            self.logger.debug(f"Generating embeddings for {len(texts)} texts")
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            embeddings = [data.embedding for data in response.data]
            self.logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)

    def embed_location(self, location: str) -> Optional[List[float]]:
        """Generate embedding for location with specific prompt engineering"""
        try:
            if not location:
                return None
                
            # Format location for better embedding
            location_prompt = (
                f"geographical location: {location.lower().strip()} "
                f"area coordinates region place locality"
            )
            
            self.logger.debug(f"Generating location embedding for: {location}")
            embedding = self.embed_text(location_prompt)
            
            if embedding:
                self.logger.info(f"Successfully generated location embedding")
                return embedding
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate location embedding: {e}")
            return None

def test_text_embedder(skills: Union[str, List[str]]) -> None:
    logger = CustomLogger("TextEmbedderTest")
    embedder = TextEmbedder(logger=logger)
    sample_text = skills if isinstance(skills, str) else " ".join(skills)
    embedding = embedder.embed_text(sample_text)
    if embedding:
        logger.info(f"Embedding length: {len(embedding)}")
        print("Sample embedding:", embedding[:10], "...")  # Print first 10 values for brevity
    else:
        logger.error("Embedding generation failed.")
