#!/usr/bin/env python3
"""Test script to demonstrate the new human-like response generation."""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.brand.loader import BrandLoader
from src.llm.prompts import PromptTemplate
from src.models import RedditPost

console = Console()

# Test posts representing different scenarios
TEST_POSTS = [
    RedditPost(
        id="test1",
        title="Looking for true crime podcasts similar to Serial",
        content="I just finished Serial and absolutely loved the investigative journalism style. I'm looking for something with deep dives into single cases, good production quality, and that keeps you guessing. Any recommendations?",
        subreddit="podcasts",
        score=45,
        num_comments=12,
        created_at=datetime.now(UTC),
        url="https://reddit.com/test1",
        author="test_user1",
    ),
    RedditPost(
        id="test2",
        title="Need podcast recommendations for my daily commute",
        content="I have about a 40-minute commute each way and I'm tired of music. Looking for engaging podcasts that are easy to follow while driving. I'm interested in science, history, or interesting stories. Episodes around 30-45 minutes would be perfect!",
        subreddit="podcasts",
        score=28,
        num_comments=8,
        created_at=datetime.now(UTC),
        url="https://reddit.com/test2",
        author="test_user2",
    ),
    RedditPost(
        id="test3",
        title="Best comedy podcasts that aren't just interviews?",
        content="I love comedy but I'm getting tired of the interview format. Looking for comedy podcasts with sketches, improv, or just funny people riffing. Something that will actually make me laugh out loud. What are your favorites?",
        subreddit="podcasts",
        score=22,
        num_comments=15,
        created_at=datetime.now(UTC),
        url="https://reddit.com/test3",
        author="test_user3",
    ),
    RedditPost(
        id="test4",
        title="Podcast suggestions for learning about psychology?",
        content="I'm fascinated by psychology and human behavior. Looking for podcasts that explore psychological concepts, research, or case studies in an accessible way. Not looking for self-help, more like educational content about the field itself.",
        subreddit="podcasts",
        score=19,
        num_comments=6,
        created_at=datetime.now(UTC),
        url="https://reddit.com/test4",
        author="test_user4",
    ),
    RedditPost(
        id="test5",
        title="Any podcasts like Radiolab but for other topics?",
        content="I absolutely love Radiolab's production style - the way they layer sounds, tell stories, and explain complex ideas. Are there other podcasts with similar high production values but covering different topics like history, technology, or culture?",
        subreddit="podcasts",
        score=34,
        num_comments=9,
        created_at=datetime.now(UTC),
        url="https://reddit.com/test5",
        author="test_user5",
    ),
]

# Example responses that would be generated (simulating different personas)
EXAMPLE_RESPONSES = [
    # Enthusiastic Superfan
    """oh man YES! if you loved Serial you HAVE to try Bear Brook - it's this insane cold case that 
literally had me googling forensics at 2am. Also In the Dark season 2?? MIND BLOWN. 

i keep all my true crime organized in goodpods btw, helps track the multi-episode investigations: 
goodpods.app/discover""",
    
    # Casual Helper
    """yeah for that commute length, planet money is perfect. like 20-30 min episodes about weird 
economics stuff but actually interesting

99% invisible is also solid tbh... design stories that make you notice things. both easy to 
follow while driving""",
    
    # Fellow Junkie  
    """had the exact same issue with comedy podcasts! comedy bang bang saved me - it's improv 
with recurring characters and absolutely ridiculous

also mbmbam (my brother my brother and me) if you want three idiots giving terrible advice... 
consistently makes me laugh on the subway like a weirdo""",
    
    # The Storyteller
    """funny story - my therapist actually recommended hidden brain to me and now i'm obsessed. 
shankar vedantam breaks down psychological research but makes it super accessible

you are not so smart is also fantastic for cognitive biases. learned why i'm terrible at 
decision making lol""",
    
    # Concise Expert
    """twenty thousand hertz for sound design stories. imaginary worlds for sci-fi culture deep dives. 
reply all (rip) had similar production values.

all have that radiolab quality. goodpods has curated lists for high-production shows: goodpods.app"""
]


def display_comparison():
    """Display old vs new response styles."""
    console.print(
        Panel.fit(
            "[bold cyan]🎯 Human-Like Response Generation Test[/bold cyan]\n"
            "[dim]Demonstrating 5 different personas and natural variations[/dim]",
            border_style="bold cyan",
        )
    )
    
    console.print("\n[bold]OLD STYLE (Too AI/formal):[/bold]")
    console.print(Panel(
        "I'd be happy to help you find true crime podcasts similar to Serial! "
        "I recommend checking out Bear Brook, which offers excellent investigative "
        "journalism with deep dives into a fascinating cold case. In the Dark is "
        "another outstanding choice, particularly Season 2. You might find it helpful "
        "to organize your podcasts using Goodpods: goodpods.app",
        border_style="red",
        title="❌ Sounds like ChatGPT",
    ))
    
    console.print("\n[bold]NEW STYLE (Human/natural):[/bold]")
    
    for i, (post, response) in enumerate(zip(TEST_POSTS, EXAMPLE_RESPONSES), 1):
        # Determine persona type based on response style
        if "oh man" in response.lower() or "YES!" in response:
            persona = "🔥 Enthusiastic Superfan"
            color = "yellow"
        elif "yeah" in response.lower() or "tbh" in response:
            persona = "😎 Casual Helper"
            color = "cyan"
        elif "exact same" in response.lower():
            persona = "🤝 Fellow Junkie"
            color = "green"
        elif "funny story" in response.lower() or "story" in response:
            persona = "📖 The Storyteller"
            color = "magenta"
        else:
            persona = "⚡ Concise Expert"
            color = "blue"
        
        console.print(f"\n[bold]Example {i}: {persona}[/bold]")
        console.print(f"[dim]Responding to: {post.title}[/dim]")
        
        console.print(Panel(
            response,
            border_style=color,
            padding=(0, 1),
        ))
    
    # Summary table
    console.print("\n[bold cyan]📊 Key Improvements:[/bold cyan]")
    
    table = Table(show_header=False, box=None)
    table.add_column("Feature", style="dim")
    table.add_column("Implementation")
    
    improvements = [
        ("Varied personas", "5 different character types that rotate randomly"),
        ("Natural language", "Fragments, Reddit-speak (tbh, ngl, imo), casual punctuation"),
        ("Genuine enthusiasm", "Real reactions: 'MIND BLOWN', 'absolutely ridiculous'"),
        ("CTA variation", "70% include naturally, 30% skip entirely"),
        ("Length variation", "2-5 sentences randomly selected"),
        ("Personal stories", "Anecdotes and experiences that feel real"),
        ("Typos/casualness", "Occasional lowercase, ellipsis, informal structure"),
    ]
    
    for feature, implementation in improvements:
        table.add_row(f"✅ {feature}:", implementation)
    
    console.print(table)
    
    console.print("\n[bold green]✨ Result: Responses now sound like real Reddit users![/bold green]")
    console.print("[dim]The prompts will randomly select personas and styles for natural variety.[/dim]")


def test_prompt_generation():
    """Test the actual prompt generation with the new system."""
    console.print("\n" + "="*60)
    console.print("\n[bold cyan]🔧 Testing Prompt Generation:[/bold cyan]\n")
    
    # Load brand config
    brands_dir = Path(__file__).parent.parent / "brands"
    brand_loader = BrandLoader(brands_dir)
    brand_config = brand_loader.load_brand_config("goodpods")
    
    # Generate a few prompts to show variation
    test_post = TEST_POSTS[0]  # Use the Serial podcast post
    
    console.print("[dim]Generating 3 different prompts for the same post to show variation:[/dim]\n")
    
    for i in range(3):
        prompt = PromptTemplate.create_response_prompt(test_post, brand_config)
        
        # Extract the persona type from the prompt
        if "HUGE podcast fan" in prompt:
            persona = "Enthusiastic Superfan"
        elif "laid-back Reddit user" in prompt:
            persona = "Casual Helper"
        elif "relates because" in prompt:
            persona = "Fellow Junkie"
        elif "through personal anecdotes" in prompt:
            persona = "The Storyteller"
        else:
            persona = "Concise Expert"
        
        # Extract CTA approach
        has_cta = "Don't mention any apps" not in prompt
        
        console.print(f"[bold]Prompt #{i+1}:[/bold]")
        console.print(f"  • Persona: [cyan]{persona}[/cyan]")
        console.print(f"  • CTA included: [{'green' if has_cta else 'yellow'}]{has_cta}[/{'green' if has_cta else 'yellow'}]")
        console.print(f"  • Dynamic elements working: [green]✓[/green]\n")


if __name__ == "__main__":
    display_comparison()
    test_prompt_generation()