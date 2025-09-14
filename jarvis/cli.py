import os
import socket
import click
from rich.console import Console

# Import command groups
from jarvis.commands import (
    git_manager,
    port_checker,
    process_killer,
    system_monitor,
    file_transfer,
    commit_helper,
    db_explorer,
)

console = Console()


@click.group()
def cli():
    """[bold cyan]Jarvis – Your Development Assistant[/bold cyan]"""
    pass


# ----------------- REGISTER COMMAND GROUPS ----------------- #
cli.add_command(git_manager.git_manager, name="git-manager")
cli.add_command(port_checker.port_checker, name="port-checker")
cli.add_command(process_killer.process_killer, name="process-killer")
cli.add_command(system_monitor.system_monitor, name="system-monitor")
cli.add_command(file_transfer.file_transfer, name="file-transfer")
cli.add_command(commit_helper.commit_helper, name="commit-helper")
cli.add_command(db_explorer.db_explorer, name="db-explorer")


# ----------------- BASIC COMMANDS ----------------- #
@cli.command()
def hello():
    """Say hello from Jarvis"""
    console.print("[bold green]Hello — I am Jarvis! Ready to assist you 🚀[/bold green]")


@cli.command()
@click.option("--verbose", is_flag=True, help="Run extended checks (test saved configs and connectivity)")
def diagnostics(verbose):
    """Run system diagnostics to verify installed modules and saved configs"""
    console.print("[bold cyan]Running Jarvis diagnostics...[/bold cyan]")

    # --- Git Manager check ---
    try:
        from jarvis.utils import git_utils

        try:
            git_utils.init_db()
            console.print("[green]✔ Git Manager: DB initialized[/green]")
        except Exception as e:
            console.print(f"[yellow]! Git Manager: init_db raised warning: {e}[/yellow]")

    except Exception as e:
        console.print(f"[red]✘ Git Manager import failed: {e}[/red]")

    # --- psutil check ---
    try:
        import psutil

        # quick call to ensure psutil works
        try:
            psutil.cpu_percent(interval=0.1)
            console.print("[green]✔ psutil: Available (Port Checker, Process Killer, System Monitor OK)[/green]")
        except Exception as e:
            console.print(f"[yellow]! psutil imported but runtime call failed: {e}[/yellow]")
    except Exception as e:
        console.print(f"[red]✘ psutil import failed: {e}[/red]")

    # --- socket check ---
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.close()
        console.print("[green]✔ socket: Available (LAN transfers OK)[/green]")
    except Exception as e:
        console.print(f"[red]✘ socket failed: {e}[/red]")

    # --- Paramiko (SFTP) check ---
    try:
        import paramiko  # noqa: F401

        console.print("[green]✔ paramiko: Available (SFTP OK)[/green]")
    except Exception as e:
        console.print(f"[red]✘ paramiko import failed: {e}[/red]")

    # --- smbprotocol (SMB) check ---
    try:
        import smbprotocol  # noqa: F401

        console.print("[green]✔ smbprotocol: Available (SMB OK)[/green]")
    except Exception as e:
        console.print(f"[yellow]! smbprotocol not available: {e}[/yellow]")

    # ----------------- EXTENDED CONFIG CHECKS ----------------- #
    if verbose:
        console.print("\n[bold cyan]Running extended configuration checks...[/bold cyan]")

        # File-transfer config checks
        try:
            from jarvis.utils import file_utils

            ft_cfg = file_utils.load_config()
            if not ft_cfg:
                console.print("[yellow]ℹ No file-transfer config saved. Skipping file-transfer checks.[/yellow]")
            else:
                console.print(f"[cyan]File-transfer config found (mode={ft_cfg.get('mode')}):[/cyan] { {k: ('********' if k=='password' else v) for k,v in ft_cfg.items()} }")

                # basic validations per mode
                if ft_cfg.get("mode") == "local":
                    src = ft_cfg.get("source")
                    dst = ft_cfg.get("destination")
                    if not src or not os.path.exists(src):
                        console.print(f"[red]✘ File-transfer local: source not found ({src})[/red]")
                    else:
                        console.print("[green]✔ File-transfer local: source exists[/green]")
                    if dst:
                        try:
                            os.makedirs(dst, exist_ok=True)
                            console.print("[green]✔ File-transfer local: destination writable/created[/green]")
                        except Exception as e:
                            console.print(f"[red]✘ File-transfer local: cannot create destination: {e}[/red]")

                elif ft_cfg.get("mode") == "network":
                    ip = ft_cfg.get("ip")
                    try:
                        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s2.settimeout(2)
                        if ip and s2.connect_ex((ip, 5001)) == 0:
                            console.print(f"[green]✔ File-transfer network: {ip}:5001 is reachable[/green]")
                        else:
                            console.print(f"[yellow]! File-transfer network: {ip}:5001 not reachable (will depend on receiver) [/yellow]")
                        s2.close()
                    except Exception as e:
                        console.print(f"[red]✘ File-transfer network check failed: {e}[/red]")

                elif ft_cfg.get("mode") == "remote":
                    ip = ft_cfg.get("ip")
                    proto = ft_cfg.get("protocol", "sftp")
                    if proto.lower() == "sftp":
                        try:
                            import paramiko

                            ssh = paramiko.SSHClient()
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            ssh.connect(ip, username=ft_cfg.get("username"), password=ft_cfg.get("password"), timeout=5)
                            sftp = ssh.open_sftp()
                            try:
                                sftp.listdir(ft_cfg.get("destination", "."))
                                console.print("[green]✔ File-transfer remote (SFTP): destination accessible[/green]")
                            except Exception:
                                console.print("[yellow]! File-transfer remote (SFTP): destination not found, but login worked[/yellow]")
                            sftp.close()
                            ssh.close()
                        except Exception as e:
                            console.print(f"[red]✘ File-transfer remote (SFTP) connection failed: {e}[/red]")
                    elif proto.lower() == "smb":
                        try:
                            import smbprotocol

                            try:
                                smbprotocol.ClientConfig(username=ft_cfg.get("username"), password=ft_cfg.get("password"))
                                console.print("[green]✔ File-transfer remote (SMB): authentication succeeded[/green]")
                            except Exception as e:
                                console.print(f"[red]✘ File-transfer remote (SMB) auth failed: {e}[/red]")
                        except Exception as e:
                            console.print(f"[red]✘ File-transfer remote (SMB) check failed: {e}[/red]")

        except Exception as e:
            console.print(f"[red]✘ File-transfer extended checks failed: {e}[/red]")

        # DB explorer config checks
        try:
            from jarvis.utils import db_utils

            db_cfg = db_utils.load_db_config()
            if not db_cfg:
                console.print("[yellow]ℹ No DB config saved. Skipping DB checks.[/yellow]")
            else:
                safe = db_cfg.copy()
                if "password" in safe:
                    safe["password"] = "********"
                console.print(f"[cyan]DB config found:[/cyan] {safe}")

                # attempt to open a connection and list tables
                try:
                    conn = db_utils.get_connection(db_cfg)
                    try:
                        tables = db_utils.list_tables(db_cfg)
                        console.print(f"[green]✔ DB connection successful — {len(tables)} table(s) found[/green]")
                    except Exception as e:
                        console.print(f"[yellow]! Connected to DB but failed to list tables: {e}[/yellow]")
                    finally:
                        try:
                            conn.close()
                        except Exception:
                            pass
                except Exception as e:
                    console.print(f"[red]DB connection failed: {e}[/red]")

        except Exception as e:
            console.print(f"[red]✘ DB extended checks failed: {e}[/red]")

    console.print("\n[bold cyan]Diagnostics complete [/bold cyan]")
