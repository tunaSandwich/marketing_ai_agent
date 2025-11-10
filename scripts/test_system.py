#!/usr/bin/env python3
"""Comprehensive system test suite."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_config_loading():
    """Test configuration loading."""
    try:
        from src.utils.config import get_settings
        settings = get_settings()
        
        # Verify all required fields
        assert settings.reddit.client_id, "Reddit client_id missing"
        assert settings.reddit.client_secret, "Reddit client_secret missing"
        assert settings.reddit.username, "Reddit username missing"
        assert settings.reddit.password, "Reddit password missing"
        assert settings.llm.api_key, "Anthropic API key missing"
        
        return True, f"User: {settings.reddit.username}"
    except Exception as e:
        return False, str(e)


def test_reddit_auth():
    """Test Reddit authentication."""
    try:
        from src.utils.config import get_settings
        from src.reddit.adapter import RedditAdapter
        
        settings = get_settings()
        adapter = RedditAdapter(settings.reddit)
        username = adapter._reddit.user.me().name
        
        return True, f"Authenticated as u/{username}"
    except Exception as e:
        return False, str(e)


def test_account_health():
    """Test Reddit account health."""
    try:
        from src.utils.config import get_settings
        from src.reddit.poster import RedditPoster
        
        settings = get_settings()
        poster = RedditPoster(settings.reddit)
        health = poster.check_account_health()
        
        if health['can_post']:
            details = f"Karma: {health['karma']}, Age: {health['account_age_days']:.0f} days"
            return True, details
        else:
            return False, health.get('reason', 'Unknown reason')
    except Exception as e:
        return False, str(e)


def test_10_percent_rule():
    """Test 10% rule compliance."""
    try:
        from src.utils.config import get_settings
        from src.reddit.poster import RedditPoster
        
        settings = get_settings()
        poster = RedditPoster(settings.reddit)
        activity = poster.get_recent_activity()
        
        if activity['safe_to_post']:
            ratio = activity['promotional_ratio']
            return True, f"Ratio: {ratio:.1%} (safe)"
        else:
            ratio = activity['promotional_ratio']
            return False, f"Ratio: {ratio:.1%} (too high!)"
    except Exception as e:
        return False, str(e)


def test_rag_system():
    """Test RAG system."""
    try:
        from src.rag.retriever import KnowledgeRetriever
        
        index_dir = Path(__file__).parent.parent / "brands" / "goodpods" / "index"
        
        if not index_dir.exists():
            return False, "Index directory not found"
        
        retriever = KnowledgeRetriever(index_dir)
        num_chunks = len(retriever.metadata)
        
        # Test retrieval
        chunks = retriever.retrieve("What is the 10% rule?", top_k=3)
        
        if not chunks:
            return False, "No chunks retrieved"
        
        # Check if reddit_rules is in results
        has_rules = any('reddit_rules' in chunk.filename for chunk in chunks)
        
        if has_rules:
            return True, f"{num_chunks} chunks, reddit_rules found"
        else:
            return True, f"{num_chunks} chunks loaded"
            
    except Exception as e:
        return False, str(e)


def test_claude_api():
    """Test Claude API connection."""
    try:
        from src.utils.config import get_settings
        from src.llm.client import ClaudeClient
        from src.models import RedditPost
        from datetime import datetime, UTC
        
        settings = get_settings()
        client = ClaudeClient(settings.llm)
        
        # Simple test generation
        test_post = RedditPost(
            id='test123',
            title='Test post',
            content='Test content',
            subreddit='test',
            score=1,
            num_comments=0,
            created_at=datetime.now(UTC),
            url='https://reddit.com/test',
            author='test_user'
        )
        
        response = client.generate_response(
            prompt='Say "test successful" in 3 words or less.',
            post_id=test_post.id,
            brand_id='test',
            response_id='test_response',
            prompt_template='test'
        )
        
        return True, f"{response.generation_time_ms}ms response time"
        
    except Exception as e:
        return False, str(e)


def test_orchestrator():
    """Test orchestrator initialization."""
    try:
        from src.orchestrator import GrowthOrchestrator
        
        orchestrator = GrowthOrchestrator(brand_id='goodpods')
        
        return True, "Initialized successfully"
        
    except Exception as e:
        return False, str(e)


def test_discovery():
    """Test Reddit discovery."""
    try:
        from src.orchestrator import GrowthOrchestrator
        
        orchestrator = GrowthOrchestrator(brand_id='goodpods')
        opportunities = orchestrator.discover_opportunities(limit=3)
        
        return True, f"Found {len(opportunities)} opportunities"
        
    except Exception as e:
        return False, str(e)




def test_engagement_system():
    """Test unified engagement system."""
    try:
        from src.utils.config import get_settings
        from src.reddit.engagement import RedditEngagementManager
        from src.brand.loader import BrandLoader
        
        settings = get_settings()
        brands_dir = Path(__file__).parent.parent / "brands"
        brand_loader = BrandLoader(brands_dir)
        brand_config = brand_loader.load_brand_config("goodpods")
        
        manager = RedditEngagementManager(
            reddit_config=settings.reddit,
            llm_config=settings.llm,
            brand_config=brand_config,
        )
        
        # Test account health check
        health = manager.get_account_health()
        
        return True, f"Engagement system ready, health: {health.health_score:.1f}/100 ({health.account_state.value})"
        
    except Exception as e:
        return False, str(e)


def run_all_tests():
    """Run all tests and display results."""
    
    console.print(Panel.fit(
        "[bold cyan]🧪 System Test Suite[/bold cyan]\n"
        "[dim]Running comprehensive pre-deployment tests...[/dim]",
        border_style="cyan"
    ))
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Reddit Authentication", test_reddit_auth),
        ("Account Health Check", test_account_health),
        ("10% Rule Compliance", test_10_percent_rule),
        ("RAG System", test_rag_system),
        ("Claude API", test_claude_api),
        ("Orchestrator Init", test_orchestrator),
        ("Reddit Discovery", test_discovery),
        ("Engagement System", test_engagement_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n[cyan]Testing:[/cyan] {test_name}...", end=" ")
        
        try:
            passed, details = test_func()
            
            if passed:
                console.print("[green]✅ PASS[/green]")
                results.append((test_name, "✅ PASS", details))
            else:
                console.print("[red]❌ FAIL[/red]")
                results.append((test_name, "❌ FAIL", details))
                
        except Exception as e:
            console.print("[red]❌ ERROR[/red]")
            results.append((test_name, "❌ ERROR", str(e)))
    
    # Display summary table
    console.print("\n")
    table = Table(title="Test Results Summary")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")
    
    for test_name, status, details in results:
        table.add_row(test_name, status, details)
    
    console.print(table)
    
    # Check overall status
    failures = [r for r in results if "FAIL" in r[1] or "ERROR" in r[1]]
    
    if failures:
        console.print("\n[bold red]❌ Some tests failed. Fix issues before deploying.[/bold red]")
        console.print("\n[yellow]Failed tests:[/yellow]")
        for test_name, status, details in failures:
            console.print(f"  • {test_name}: {details}")
        return False
    else:
        console.print("\n[bold green]✅ All tests passed! System ready for deployment.[/bold green]")
        
        # Show deployment readiness summary
        console.print("\n")
        deployment_panel = Panel.fit(
            "[bold green]🚀 DEPLOYMENT READY[/bold green]\n\n"
            "[yellow]Auto-posting Configuration:[/yellow]\n"
            "• Account age requirement: 30+ days\n"
            "• Auto-post threshold: 8.0/10 quality score\n"
            "• Auto-reject: <8.0/10 scores (hands-off mode)\n\n"
            "[yellow]Safety Mechanisms Active:[/yellow]\n"
            "• Account health monitoring\n"
            "• 10% promotional ratio enforcement\n"
            "• RAG safety rules integration\n"
            "• Enhanced decision logging\n"
            "• Engagement maintenance system\n\n"
            "[yellow]Schedule:[/yellow]\n"
            "• Discovery + Auto-post: Every 1 hour\n"
            "• Engagement: Every 2 hours at :15",
            border_style="green",
            title="System Status"
        )
        console.print(deployment_panel)
        
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)