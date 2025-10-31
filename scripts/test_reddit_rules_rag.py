#!/usr/bin/env python3
"""Test that reddit_rules.md is being retrieved by RAG."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from src.rag.retriever import KnowledgeRetriever

console = Console()

def main():
    index_dir = Path(__file__).parent.parent / "brands" / "goodpods" / "index"
    retriever = KnowledgeRetriever(index_dir)
    
    # Test queries that should trigger reddit rules
    test_queries = [
        "How often should I post promotional content?",
        "What are the spam rules on Reddit?",
        "Can I mention Goodpods in every response?",
        "How many comments before mentioning the app?",
        "What is the 10% rule on Reddit?",
    ]
    
    for query in test_queries:
        console.print(f"\n[bold cyan]Query:[/bold cyan] {query}")
        chunks = retriever.retrieve(query, top_k=3)
        
        found_reddit_rules = False
        for chunk in chunks:
            console.print(f"  📄 {chunk.filename} (similarity: {chunk.similarity:.2f})")
            if "reddit_rules" in chunk.filename:
                found_reddit_rules = True
                console.print(f"  [green]✓ Reddit rules retrieved![/green]")
                console.print(f"  [dim]Content preview: {chunk.content[:100]}...[/dim]")
        
        if not found_reddit_rules:
            console.print(f"  [red]✗ Reddit rules not retrieved for this query[/red]")

if __name__ == "__main__":
    main()