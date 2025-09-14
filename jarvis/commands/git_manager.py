import click
from rich.console import Console
from rich.table import Table

from jarvis.utils import git_utils

console = Console()

@click.group()
def git_manager():
    """Manage your Git branches with metadata"""
    pass


@git_manager.command("add-branch")
@click.option("--name", prompt="Branch name", help="Name of the git branch")
@click.option("--commit-hash", "commit_hash", prompt="Commit hash", help="Latest commit hash")
@click.option("--issue", prompt="Issue ID", help="Related issue/ticket ID")
@click.option("--desc", prompt="Description", help="Short description")
def add_branch(name, commit_hash, issue, desc):
    """Add a new branch record"""
    from jarvis.utils import git_utils
    git_utils.add_branch(name, commit_hash, issue, desc)
    console.print(f"[green]Branch '{name}' added successfully![/green]")

@git_manager.command("list-branches")
def list_branches():
    """List all branches with metadata"""
    from jarvis.utils import git_utils
    branches = git_utils.list_branches()

    if not branches:
        console.print("[yellow]No branches found![/yellow]")
        return

    table = Table(title="Tracked Git Branches", show_lines=True)
    table.add_column("ID", style="cyan", justify="center")
    table.add_column("Name", style="green")
    table.add_column("Commit", style="magenta")
    table.add_column("Issue ID", style="blue")
    table.add_column("Description", style="white")
    table.add_column("Status", style="bold")

    for b in branches:
        branch_id, name, commit_hash, issue_id, desc, status = b

        # 🎨 Add colors to status
        if status.lower() == "open":
            status_display = "[green]OPEN[/green]"
        elif status.lower() == "merged":
            status_display = "[yellow]MERGED[/yellow]"
        elif status.lower() == "closed":
            status_display = "[red]CLOSED[/red]"
        else:
            status_display = status

        # Truncate commit hash to first 7 chars like Git
        short_commit = commit_hash[:7] if commit_hash else "-"

        table.add_row(
            str(branch_id),
            name,
            short_commit,
            issue_id if issue_id else "-",
            desc if desc else "-",
            status_display
        )

    console.print(table)

@git_manager.command("delete-branch")
@click.argument("branch_id", type=int)
def delete_branch(branch_id):
    """Delete a branch record by ID"""
    from jarvis.utils import git_utils
    git_utils.delete_branch(branch_id)
    console.print(f"[red]Branch {branch_id} deleted successfully![/red]")


@git_manager.command("update-status")
@click.argument("branch_id", type=int)
@click.argument("status", type=click.Choice(["open", "merged", "closed"], case_sensitive=False))
def update_status(branch_id, status):
    """Update status of a branch"""
    git_utils.update_branch_status(branch_id, status)
    console.print(f"[cyan]Branch {branch_id} status updated to '{status}'.[/cyan]")
