import click
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from pathlib import Path
from jarvis.utils import db_utils

console = Console()

@click.group()
def db_explorer():
    """Explore SQLite and Postgres databases"""
    pass


# ---------------- connect ---------------- #
@db_explorer.command("connect")
@click.option("--db", type=click.Choice(["sqlite", "postgres"], case_sensitive=False), prompt=True)
@click.option("--path", help="SQLite DB file path (for sqlite)")
@click.option("--host", help="Postgres host (for postgres)")
@click.option("--port", type=int, help="Postgres port (default 5432)", default=5432)
@click.option("--user", help="Postgres username")
@click.option("--password", help="Postgres password", hide_input=True)
@click.option("--dbname", help="Postgres database name")
def connect(db, path, host, port, user, password, dbname):
    """Save connection settings for a database"""
    cfg = {"type": db}
    if db == "sqlite":
        if not path:
            path = click.prompt("SQLite DB file path", type=str)
        cfg["path"] = str(Path(path).expanduser())
        if not Path(cfg["path"]).exists():
            console.print(f"[yellow]Notice: {cfg['path']} does not exist yet (it will be created on first write).[/yellow]")
    else:
        # postgres prompts
        host = host or click.prompt("Host", default="localhost")
        port = port or click.prompt("Port", default=5432, type=int)
        user = user or click.prompt("Username")
        password = password or click.prompt("Password", hide_input=True)
        dbname = dbname or click.prompt("Database name")
        cfg.update({"host": host, "port": port, "user": user, "password": password, "dbname": dbname})

    db_utils.save_db_config(cfg)
    console.print(f"[green]Saved DB config:[/green] {cfg}")


# ---------------- tables ---------------- #
@db_explorer.command("tables")
def tables():
    """List tables in configured DB"""
    try:
        tbls = db_utils.list_tables()
        if not tbls:
            console.print("[yellow]No tables found.[/yellow]")
            return
        table = Table(title="Tables")
        table.add_column("Name", style="cyan")
        for t in tbls:
            table.add_row(t)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing tables: {e}[/red]")


# ---------------- query ---------------- #
@db_explorer.command("query")
@click.argument("sql", required=True)
@click.option("--limit", type=int, default=50, help="Rows to fetch (SELECT)")
@click.option("--export", type=click.Choice(["csv", "json"], case_sensitive=False), required=False)
@click.option("--out", help="Export file path (if --export used)")
@click.option("--show-sql", is_flag=True, help="Show SQL before running")
def query(sql, limit, export, out, show_sql):
    """Run SQL against the configured DB (provide a SELECT to return rows)"""
    try:
        if show_sql:
            console.print("[bold]SQL to run:[/bold]")
            console.print(Syntax(sql, "sql", line_numbers=False))

        cols, rows = db_utils.run_query(sql, fetch_limit=limit)
        if not cols:
            console.print("[green]Query executed (no rows returned).[ /green]")
            return

        # show limited preview
        t = Table(show_header=True, header_style="bold magenta")
        for c in cols:
            t.add_column(str(c))
        for r in rows:
            t.add_row(*[str(c) for c in r])
        console.print(t)

        if export:
            if not out:
                out = click.prompt("Export file path", type=str)
            outpath = db_utils.export_results(cols, rows, out, export)
            console.print(f"[green]Exported to {outpath}[/green]")

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")


# ---------------- search ---------------- #
@db_explorer.command("search")
@click.argument("keyword", required=True)
@click.option("--limit", default=10, help="Rows per table to return")
def search(keyword, limit):
    """Search keyword across textual columns in all tables"""
    try:
        results = db_utils.search_keyword(keyword, limit_per_table=limit)
        if not results:
            console.print("[yellow]No matches found.[/yellow]")
            return
        for table_name, (cols, rows) in results.items():
            console.print(f"\n[bold cyan]Table:[/bold cyan] {table_name}  —  [green]{len(rows)} rows matched[/green]")
            t = Table(show_header=True, header_style="bold magenta")
            for c in cols:
                t.add_column(str(c))
            for r in rows:
                t.add_row(*[str(c) for c in r])
            console.print(t)
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")


# ---------------- show-config & reset ---------------- #
@db_explorer.command("show-config")
def show_config():
    cfg = db_utils.load_db_config()
    if not cfg:
        console.print("[yellow]No DB config saved.[/yellow]")
    else:
        safe = cfg.copy()
        if "password" in safe:
            safe["password"] = "********"
        console.print(f"[cyan]Saved DB config:[/cyan] {safe}")


@db_explorer.command("reset")
def reset():
    ok = db_utils.clear_db_config()
    if ok:
        console.print("[green]DB config cleared.[/green]")
    else:
        console.print("[yellow]No config to clear.[/yellow]")
