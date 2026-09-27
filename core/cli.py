import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.scanner import get_snapshot
from core.analyzer import analyze_impersonation
from core.exporter import export_to_json

console = Console()

@click.group()
def cli():
    """ANUSINT: Advanced Anti-Impersonation OSINT Tool"""
    pass

@cli.command()
@click.argument('username')
@click.option('--export', is_flag=True, help='Export the snapshot data to a JSON file.')
def snapshot(username, export):
    """Capture and display an Instagram profile snapshot."""
    with console.status(f"[bold cyan]Bypassing rate limits & querying data for @{username}...[/bold cyan]", spinner="dots"):
        try:
            profile = get_snapshot(username)
            
            # Build Terminal Table
            table = Table(title=f"Profile Snapshot: @{profile.username}")
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")
            
            table.add_row("Full Name", profile.full_name)
            table.add_row("Followers", str(profile.followers))
            table.add_row("Following", str(profile.following))
            table.add_row("Private", "Yes" if profile.is_private else "No")
            table.add_row("Verified", "[green]Yes[/green]" if profile.is_verified else "No")
            table.add_row("Bio", profile.biography)
            if profile.external_url:
                table.add_row("Link", profile.external_url)
                
            console.print(table)
            
            if export:
                # Convert dataclass to dict for export
                data = profile.__dict__
                filepath = export_to_json(username, data)
                console.print(f"[bold green]✓ Exported to {filepath}[/bold green]")
                
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

@cli.command()
@click.argument('original_username')
@click.argument('suspect_username')
@click.option('--export', is_flag=True, help='Export the analysis report to a JSON file.')
def compare(original_username, suspect_username, export):
    """Analyze a suspect profile against the original for impersonation."""
    with console.status(f"[bold cyan]Fetching profiles and analyzing impersonation risk...[/bold cyan]", spinner="dots"):
        try:
            original = get_snapshot(original_username)
            suspect = get_snapshot(suspect_username)
            
            analysis = analyze_impersonation(original, suspect)
            
            # Format output color based on risk level
            risk_color = "green"
            if analysis['risk_level'] == "CRITICAL":
                risk_color = "red"
            elif analysis['risk_level'] == "HIGH":
                risk_color = "orange3"
            elif analysis['risk_level'] == "MODERATE":
                risk_color = "yellow"
                
            console.print(Panel(
                f"Risk Level: [bold {risk_color}]{analysis['risk_level']}[/bold {risk_color}]\n"
                f"Risk Score: [bold]{analysis['risk_score']}/100[/bold]\n"
                f"Name Match: {analysis['metrics']['name_similarity']*100:.0f}%\n"
                f"Bio Match: {analysis['metrics']['bio_similarity']*100:.0f}%\n"
                f"Suspicious Follower Disparity: {'[red]Yes[/red]' if analysis['metrics']['follower_disparity_flag'] else 'No'}",
                title=f"Impersonation Report: @{suspect_username}",
                expand=False
            ))
            
            if export:
                filepath = export_to_json(suspect_username, analysis)
                console.print(f"[bold green]✓ Exported to {filepath}[/bold green]")
                
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == '__main__':
    cli()