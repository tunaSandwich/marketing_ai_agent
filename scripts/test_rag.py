#!/usr/bin/env python3
"""Test RAG retrieval system."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from src.rag.retriever import KnowledgeRetriever


def main():
    console = Console()
    
    console.print(
        Panel.fit(
            "[bold cyan]🔍 RAG Retrieval System Test[/bold cyan]\n"
            "[dim]Testing semantic search for Goodpods knowledge[/dim]",
            border_style="bold cyan",
        )
    )
    
    # Initialize retriever
    index_dir = Path(__file__).parent.parent / "brands" / "goodpods" / "index"
    
    if not index_dir.exists():
        console.print("[red]❌ No index found. Run: python scripts/index_brand_knowledge.py[/red]")
        return
    
    try:
        retriever = KnowledgeRetriever(index_dir)
        console.print("[green]✅ Retriever initialized successfully[/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Error initializing retriever: {e}[/red]")
        return
    
    # Test queries that should trigger Goodpods knowledge
    test_queries = [
        "I need help organizing my podcasts",
        "What's a good podcast app for discovering new shows?",
        "How do I keep track of which episode I'm on?",
        "Looking for true crime podcasts",
        "I want to find podcasts through friends",
        "How should I mention Goodpods on Reddit?",
        "What makes Spotify bad for podcast discovery?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        console.print(f"[bold]Test {i}: [cyan]{query}[/cyan][/bold]")
        
        chunks = retriever.retrieve(query, top_k=3, min_similarity=0.3)
        
        if chunks:
            for j, chunk in enumerate(chunks, 1):
                color = "green" if chunk.similarity > 0.6 else "yellow" if chunk.similarity > 0.4 else "red"
                console.print(
                    Panel(
                        f"{chunk.content}\n\n[dim]Similarity: {chunk.similarity:.3f}[/dim]",
                        title=f"Result {j}: {chunk.filename}",
                        border_style=color,
                        padding=(0, 1),
                    )
                )
        else:
            console.print("[yellow]No relevant chunks found[/yellow]")
        
        console.print("")  # Spacing
    
    # Test Reddit post simulation
    console.print("[bold magenta]📝 Reddit Post Simulation:[/bold magenta]")
    
    post_title = "Looking for true crime podcasts similar to Serial"
    post_content = """I just finished Serial and absolutely loved the investigative journalism style. 
    I'm looking for something with deep dives into single cases, good production quality, and that keeps you guessing. 
    Any recommendations?"""
    
    console.print(f"[dim]Title: {post_title}[/dim]")
    console.print(f"[dim]Content: {post_content}[/dim]\n")
    
    chunks = retriever.retrieve_for_post(post_title, post_content, top_k=3, min_similarity=0.3)
    
    if chunks:
        console.print(f"[green]Retrieved {len(chunks)} relevant knowledge chunks:[/green]")
        for i, chunk in enumerate(chunks, 1):
            relevance = "🔥 High" if chunk.similarity > 0.6 else "⚡ Medium" if chunk.similarity > 0.4 else "💡 Low"
            console.print(f"  {relevance} ({chunk.similarity:.3f}): {chunk.filename}")
    else:
        console.print("[yellow]No relevant knowledge found for this post[/yellow]")


if __name__ == "__main__":
    main()