import click
from rich.console import Console
from anusint.net import fetch_profile_data

console = Console()

@click.group()
def cli():
    """ANUSINT: Advanced Anti-Impersonation Analysis Tool"""
    pass

@cli.command()
@click.argument('username')
def snapshot(username):
    """Capture and analyze a profile snapshot."""
    with console.status(f"[bold cyan]Querying data for @{username}...[/bold cyan]", spinner="dots"):
        try:
            data = fetch_profile_data(username)
            console.print(f"[bold green]✓ Snapshot successful for @{username}[/bold green]")
            # Future integration: Pass 'data' to profile_snapshot.py for deep analysis
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == '__main__':
    cli()