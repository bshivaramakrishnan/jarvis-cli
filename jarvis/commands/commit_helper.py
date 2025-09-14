import click
from rich.console import Console
from rich.syntax import Syntax
from jarvis.utils import commit_utils
import subprocess

console = Console()


@click.group()
def commit_helper():
    """AI-powered Commit Message Generator"""
    pass


@commit_helper.command("generate")
@click.option("--all", "all_changes", is_flag=True, help="Include unstaged changes")
@click.option("--scope", help="Optional commit scope (e.g., cli, db, api)")
@click.option("--commit", is_flag=True, help="Run 'git commit -m <message>' automatically")
@click.option("--show-diff", is_flag=True, help="Display the git diff being analyzed")
def generate(all_changes, scope, commit, show_diff):
    """Generate a commit message using AI (with fallback if AI unavailable)"""
    diff = commit_utils.get_git_diff(all_changes)

    if not diff:
        console.print("[yellow]⚠ No changes detected in git diff[/yellow]")
        return

    # Optional: Show the diff before analysis
    if show_diff:
        console.print("[bold magenta]Git Diff Being Analyzed:[/bold magenta]")
        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
        console.print(syntax)

    # Try AI first
    message = commit_utils.ai_commit_message(diff, scope=scope)

    if not message:
        console.print("[yellow]⚠ No API key found. Falling back to rule-based commit message[/yellow]")
        message = commit_utils.rule_based_commit(diff)

    elif message.startswith("[AI Fallback:"):
        # Extract error reason inside brackets
        error_reason = message.split("]")[0].replace("[AI Fallback:", "").strip()
        fallback_msg = message.split("] ", 1)[-1]

        console.print(f"[yellow]⚠ AI request failed: {error_reason}[/yellow]")
        console.print(f"[cyan]Fallback Commit Message:[/cyan] {fallback_msg}")
        message = fallback_msg  # use fallback only

    else:
        console.print(f"[bold cyan]Suggested Commit Message:[/bold cyan] {message}")

    if commit:
        try:
            subprocess.run(["git", "commit", "-m", message], check=True)
            console.print(f"[green]✔ Commit created:[/green] {message}")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✘ Failed to commit: {e}[/red]")
