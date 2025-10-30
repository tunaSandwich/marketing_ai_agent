#!/usr/bin/env python3
"""Index brand knowledge for RAG retrieval."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.brand.loader import BrandLoader
from src.rag.embedder import DocumentEmbedder


def main(brand_id: str = "goodpods"):
    """Index knowledge for a brand.
    
    Args:
        brand_id: Brand to index
    """
    logger.info(f"Indexing knowledge for brand: {brand_id}")
    
    # Load brand
    brands_dir = Path(__file__).parent.parent / "brands"
    loader = BrandLoader(brands_dir)
    brand_config = loader.load_brand_config(brand_id)
    
    # Load knowledge documents
    logger.info("Loading knowledge documents...")
    knowledge = loader.load_knowledge(brand_id)
    
    if not knowledge:
        logger.error(f"No knowledge documents found for {brand_id}")
        return
        
    logger.info(f"Loaded {len(knowledge)} documents")
    
    # Create embedder
    embedder = DocumentEmbedder()
    
    # Index documents
    index, metadata = embedder.index_documents(
        knowledge,
        chunk_size=300,
        chunk_overlap=50,
    )
    
    # Save index
    output_dir = brands_dir / brand_id / "index"
    embedder.save_index(index, metadata, output_dir)
    
    logger.info(f"✅ Successfully indexed {len(metadata)} chunks")
    logger.info(f"   Index saved to: {output_dir}")


if __name__ == "__main__":
    import sys
    brand_id = sys.argv[1] if len(sys.argv) > 1 else "goodpods"
    main(brand_id)