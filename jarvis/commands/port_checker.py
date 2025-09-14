import click
from rich.console import Console
from jarvis.utils import system_utils

console = Console()

@click.group()
def port_checker():
    """Check port usage on your system"""
    pass

@port_checker.command("check")
@click.argument("port", type=int)
def check(port):
    """Check which process is using a specific port"""
    result = system_utils.check_port(port)
    if result:
        console.print(f"[yellow]Port {port} is in use[/yellow]")
        console.print(f"PID: {result['pid']}, Name: {result['name']}, User: {result['user']}, Status: {result['status']}")
    else:
        console.print(f"[green]Port {port} is free[/green]")
