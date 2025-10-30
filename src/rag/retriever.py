"""Semantic search and retrieval for brand knowledge."""

from pathlib import Path
from typing import List, Optional
import pickle

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from loguru import logger
from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    """A retrieved knowledge chunk."""
    
    filename: str
    content: str
    similarity: float
    

class KnowledgeRetriever:
    """Retrieves relevant knowledge chunks using semantic search."""
    
    def __init__(
        self,
        index_dir: Path,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """Initialize retriever with pre-built index.
        
        Args:
            index_dir: Directory containing faiss.index and metadata.pkl
            model_name: Sentence transformer model name (must match indexing)
        """
        self.model = SentenceTransformer(model_name)
        
        # Load index
        index_path = index_dir / "faiss.index"
        if not index_path.exists():
            raise FileNotFoundError(f"Index not found: {index_path}")
            
        self.index = faiss.read_index(str(index_path))
        logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
        
        # Load metadata
        metadata_path = index_dir / "metadata.pkl"
        with metadata_path.open('rb') as f:
            self.metadata = pickle.load(f)
            
        logger.info(f"Loaded {len(self.metadata)} chunk metadata entries")
    
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.3,
    ) -> List[RetrievedChunk]:
        """Retrieve most relevant chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
            
        Returns:
            List of retrieved chunks with similarity scores
        """
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search index
        distances, indices = self.index.search(
            query_embedding.astype('float32'),
            top_k,
        )
        
        # Convert L2 distances to similarity scores (0-1)
        # Lower distance = higher similarity
        # Normalize to 0-1 range
        max_distance = 4.0  # Typical max for normalized embeddings
        similarities = 1 - (distances[0] / max_distance)
        similarities = np.clip(similarities, 0, 1)
        
        # Build results
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if similarity >= min_similarity:
                filename, content = self.metadata[idx]
                results.append(
                    RetrievedChunk(
                        filename=filename,
                        content=content,
                        similarity=float(similarity),
                    )
                )
        
        logger.debug(
            f"Retrieved {len(results)} chunks for query '{query[:50]}...'"
        )
        
        return results
    
    def retrieve_for_post(
        self,
        post_title: str,
        post_content: str,
        top_k: int = 3,
        min_similarity: float = 0.3,
    ) -> List[RetrievedChunk]:
        """Retrieve relevant knowledge for a Reddit post.
        
        Args:
            post_title: Post title
            post_content: Post body
            top_k: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of relevant knowledge chunks
        """
        # Combine title and content for query
        query = f"{post_title}\n\n{post_content}"
        
        return self.retrieve(query, top_k, min_similarity)