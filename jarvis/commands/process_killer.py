import click
from rich.console import Console
from rich.table import Table
from jarvis.utils import system_utils

console = Console()

@click.group()
def process_killer():
    """Search and kill processes (cross-platform)."""
    pass


@process_killer.command("search-name")
@click.argument("name", type=str)
def search_by_name(name):
    """Search processes by name"""
    results = system_utils.search_process_by_name(name)
    if not results:
        console.print(f"[yellow]No processes found with name '{name}'.[/yellow]")
        return

    table = Table(title=f"Processes matching '{name}'")
    table.add_column("PID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("User", style="blue")
    table.add_column("Status", style="magenta")

    for proc in results:
        table.add_row(str(proc["pid"]), proc["name"], proc["username"], proc["status"])

    console.print(table)


@process_killer.command("search-port")
@click.argument("port", type=int)
def search_by_port(port):
    """Search process by port"""
    results = system_utils.search_process_by_port(port)
    if not results:
        console.print(f"[green]No process found using port {port}[/green]")
        return

    table = Table(title=f"Processes using port {port}")
    table.add_column("PID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("User", style="blue")
    table.add_column("Status", style="magenta")

    for proc in results:
        table.add_row(str(proc["pid"]), proc["name"], proc["user"], proc["status"])

    console.print(table)


@process_killer.command("kill")
@click.argument("pid", type=int)
def kill_process(pid):
    """Kill process by PID"""
    success = system_utils.kill_process(pid)
    if success:
        console.print(f"[red]Process {pid} killed successfully![/red]")
    else:
        console.print(f"[bold yellow]Failed to kill process {pid}[/bold yellow]")
