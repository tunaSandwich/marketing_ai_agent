#!/usr/bin/env python3
"""Demo of the account warming system."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn

console = Console()

def main():
    console.print(Panel.fit(
        "[bold green]🌱 Account Warming System[/bold green]\n"
        "[dim]Automatic karma building for new Reddit accounts[/dim]",
        border_style="green"
    ))
    
    # Test account status
    console.print("\n[cyan]1. Current Account Status:[/cyan]")
    
    try:
        from src.utils.config import get_settings
        from src.reddit.poster import RedditPoster
        
        settings = get_settings()
        poster = RedditPoster(settings.reddit)
        health = poster.check_account_health()
        
        status_table = Table(title="Account Health Check")
        status_table.add_column("Metric", style="cyan")
        status_table.add_column("Current", style="yellow")
        status_table.add_column("Required", style="green")
        status_table.add_column("Status", style="bold")
        
        karma_status = "✅ Pass" if health.get('karma', 0) >= 100 else "❌ Fail"
        age_status = "✅ Pass" if health.get('account_age_days', 0) >= 30 else "❌ Fail"
        
        status_table.add_row(
            "Karma",
            str(health.get('karma', 0)),
            "100+",
            karma_status
        )
        status_table.add_row(
            "Account Age",
            f"{health.get('account_age_days', 0):.1f} days",
            "30+ days",
            age_status
        )
        
        overall_status = "Ready for posting" if health.get('can_post') else "Needs warming"
        status_table.add_row(
            "Overall",
            health.get('reason', 'Ready'),
            "All requirements met",
            "✅ Ready" if health.get('can_post') else "🌱 Warming"
        )
        
        console.print(status_table)
        
        # Show warming phases
        console.print("\n[cyan]2. Warming Phase Strategy:[/cyan]")
        
        current_karma = health.get('karma', 0)
        current_age = health.get('account_age_days', 0)
        
        if current_karma < 50:
            phase = "📈 Phase 1: Aggressive Building"
            activities = "30 upvotes + 2 helpful comments per cycle"
            goal = "Reach 50 karma quickly"
        elif current_karma < 100:
            phase = "📊 Phase 2: Moderate Building"
            activities = "20 upvotes + 1 helpful comment per cycle"
            goal = "Reach 100 karma threshold"
        else:
            phase = "⏳ Phase 3: Age Maintenance"
            activities = "15 upvotes per cycle"
            goal = "Wait for 30-day account age"
        
        phase_panel = Panel.fit(
            f"[yellow]Current Phase:[/yellow] {phase}\n"
            f"[yellow]Activities:[/yellow] {activities}\n"
            f"[yellow]Goal:[/yellow] {goal}",
            border_style="blue",
            title="Warming Strategy"
        )
        console.print(phase_panel)
        
        # Progress visualization
        console.print("\n[cyan]3. Progress Toward Requirements:[/cyan]")
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            
            karma_progress = min(100, (current_karma / 100) * 100)
            age_progress = min(100, (current_age / 30) * 100)
            
            karma_task = progress.add_task("Karma Progress", total=100)
            age_task = progress.add_task("Age Progress", total=100)
            
            progress.update(karma_task, completed=karma_progress)
            progress.update(age_task, completed=age_progress)
        
        # Show expected timeline
        console.print("\n[cyan]4. Expected Timeline:[/cyan]")
        
        timeline_table = Table(title="Warming Timeline")
        timeline_table.add_column("Days", style="cyan")
        timeline_table.add_column("Karma Target", style="yellow")
        timeline_table.add_column("Daily Activities", style="green")
        timeline_table.add_column("Status", style="bold")
        
        if current_karma < 25:
            timeline_table.add_row("1-7", "0 → 25", "30 upvotes + 2 comments", "🔥 Active")
            timeline_table.add_row("8-14", "25 → 50", "30 upvotes + 2 comments", "📈 Building")
            timeline_table.add_row("15-21", "50 → 100", "20 upvotes + 1 comment", "📊 Growing")
            timeline_table.add_row("22-30", "100+", "15 upvotes", "⏳ Aging")
        elif current_karma < 50:
            timeline_table.add_row("1-7", f"{current_karma} → 50", "30 upvotes + 2 comments", "🔥 Active")
            timeline_table.add_row("8-14", "50 → 100", "20 upvotes + 1 comment", "📊 Building")
            timeline_table.add_row("15-30", "100+", "15 upvotes", "⏳ Aging")
        elif current_karma < 100:
            timeline_table.add_row("1-7", f"{current_karma} → 100", "20 upvotes + 1 comment", "📊 Active")
            timeline_table.add_row("8-30", "100+", "15 upvotes", "⏳ Aging")
        else:
            remaining_days = max(0, 30 - current_age)
            timeline_table.add_row(f"1-{remaining_days:.0f}", "100+ (achieved)", "15 upvotes", "⏳ Active")
        
        console.print(timeline_table)
        
        # Show sample helpful comments
        console.print("\n[cyan]5. Sample Helpful Comments (No Promotion):[/cyan]")
        
        samples = [
            "For true crime, I'd recommend Criminal - great short-form stories.",
            "Comedy Bang Bang is hilarious if you like improv humor.",
            "Dan Carlin's Hardcore History is the gold standard for history pods.",
            "What genres are you interested in? That'll help narrow down recommendations.",
        ]
        
        for i, sample in enumerate(samples, 1):
            console.print(f"  {i}. [dim]\"{sample}\"[/dim]")
        
        # Show transition point
        console.print("\n[bold green]🎯 Automatic Transition[/bold green]")
        console.print("When account reaches 100+ karma AND 30+ days:")
        console.print("• System automatically switches to growth mode")
        console.print("• Begins discovering Reddit opportunities")
        console.print("• Starts generating and posting responses")
        console.print("• All warming activities stop")
        
        if not health.get('can_post'):
            console.print(f"\n[yellow]⏱️  Estimated time to readiness: {estimate_days_to_ready(current_karma, current_age)} days[/yellow]")
        else:
            console.print("\n[bold green]✅ Account is ready for growth mode![/bold green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


def estimate_days_to_ready(karma: int, age_days: float) -> int:
    """Estimate days until account meets all requirements."""
    karma_days = 0
    age_days_needed = max(0, 30 - age_days)
    
    if karma < 50:
        # Phase 1: ~3-5 karma per day
        karma_days += (50 - karma) / 4
        # Phase 2: ~2-3 karma per day  
        karma_days += (100 - 50) / 2.5
    elif karma < 100:
        # Phase 2: ~2-3 karma per day
        karma_days += (100 - karma) / 2.5
    
    return max(int(karma_days), int(age_days_needed))


if __name__ == "__main__":
    main()