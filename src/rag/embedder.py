"""Document embedding and indexing for semantic search."""

from pathlib import Path
from typing import List, Tuple
import pickle

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from loguru import logger


class DocumentEmbedder:
    """Embeds documents and creates searchable index."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedder with sentence transformer model.
        
        Args:
            model_name: HuggingFace model name for embeddings
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
    def chunk_document(
        self,
        text: str,
        chunk_size: int = 300,
        overlap: int = 50,
    ) -> List[str]:
        """Split document into overlapping chunks.
        
        Args:
            text: Document text to chunk
            chunk_size: Target characters per chunk
            overlap: Characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('. ')
                if last_period > chunk_size * 0.5:  # At least 50% through chunk
                    end = start + last_period + 1
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
            
        return chunks
    
    def index_documents(
        self,
        documents: dict[str, str],
        chunk_size: int = 300,
        chunk_overlap: int = 50,
    ) -> Tuple[faiss.Index, List[Tuple[str, str]]]:
        """Create FAISS index from documents.
        
        Args:
            documents: Dict of filename -> content
            chunk_size: Characters per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            Tuple of (FAISS index, list of (filename, chunk_text))
        """
        all_chunks = []
        chunk_metadata = []
        
        for filename, content in documents.items():
            chunks = self.chunk_document(content, chunk_size, chunk_overlap)
            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_metadata.append((filename, chunk))
                
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        
        # Generate embeddings
        embeddings = self.model.encode(
            all_chunks,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        
        # Create FAISS index
        index = faiss.IndexFlatL2(self.dimension)
        index.add(embeddings.astype('float32'))
        
        logger.info(f"Built FAISS index with {index.ntotal} vectors")
        
        return index, chunk_metadata
    
    def save_index(
        self,
        index: faiss.Index,
        metadata: List[Tuple[str, str]],
        output_dir: Path,
    ) -> None:
        """Save index and metadata to disk.
        
        Args:
            index: FAISS index to save
            metadata: Chunk metadata to save
            output_dir: Directory to save to
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        index_path = output_dir / "faiss.index"
        metadata_path = output_dir / "metadata.pkl"
        
        faiss.write_index(index, str(index_path))
        with metadata_path.open('wb') as f:
            pickle.dump(metadata, f)
            
        logger.info(f"Saved index to {index_path}")
        logger.info(f"Saved metadata to {metadata_path}")