import click
from rich.console import Console
from jarvis.utils import file_utils

console = Console()


@click.group()
def file_transfer():
    """Send and receive files across local machine, LAN, or remote"""
    pass


@file_transfer.command("setup")
@click.option(
    "--mode",
    type=click.Choice(["local", "network", "remote"], case_sensitive=False),
    prompt=True,
    help="Transfer mode: local, network, or remote",
)
@click.option(
    "--protocol",
    type=click.Choice(["sftp", "smb"], case_sensitive=False),
    required=False,
    help="Protocol for remote transfers (SFTP or SMB). Auto-detected if not provided.",
)
@click.option("--source", prompt="Source path", help="Path to file/folder to transfer")
@click.option("--destination", help="Destination path (required for local/remote)")
@click.option("--ip", help="Target IP (required for network/remote)")
@click.option("--username", help="Username (required for remote)")
@click.option("--password", hide_input=True, help="Password (required for remote)")
def setup(mode, protocol, source, destination, ip, username, password):
    """Configure a transfer setup once"""

    if mode == "local":
        if not destination:
            destination = click.prompt("Destination path", type=str)

    elif mode == "network":
        if not ip:
            ip = click.prompt("Target IP (e.g. 192.168.103.156)", type=str)

    elif mode == "remote":
        if not ip:
            ip = click.prompt("Target IP (remote machine)", type=str)
        if not username:
            username = click.prompt("Username")
        if not password:
            password = click.prompt("Password", hide_input=True)
        if not destination:
            destination = click.prompt("Destination folder on remote")

        # 🔍 Auto-detect protocol if not specified
        if not protocol:
            detected = file_utils.detect_protocol(ip)
            if detected:
                console.print(f"[cyan]Auto-detected protocol: {detected.upper()}[/cyan]")
                protocol = detected
            else:
                console.print("[yellow]Could not detect protocol automatically.[/yellow]")
                protocol = click.prompt(
                    "Please choose protocol manually",
                    type=click.Choice(["sftp", "smb"], case_sensitive=False),
                )

    config = file_utils.setup_transfer(
        mode, source, destination, ip, username, password, protocol or "sftp"
    )
    console.print(f"[green]Transfer setup saved[/green]: {config}")


@file_transfer.command("transfer")
def transfer():
    """Execute transfer based on saved setup"""
    config = file_utils.load_config()
    if not config:
        console.print("[red]No transfer config found. Run 'setup' first.[/red]")
        return

    mode = config["mode"]
    protocol = config.get("protocol", "sftp")

    try:
        if mode == "local":
            file_utils.local_transfer(config["source"], config["destination"])
            console.print(f"[green]File copied locally → {config['destination']}[/green]")

        elif mode == "network":
            file_utils.send_file_network(config["source"], config["ip"])
            console.print(f"[green]File sent to {config['ip']} successfully![/green]")

        elif mode == "remote":
            try:
                remote_path = file_utils.remote_transfer(
                    config["source"],
                    config["destination"],
                    config["ip"],
                    config["username"],
                    config["password"],
                    protocol,
                )
                console.print(f"[green]File transferred via {protocol.upper()} → {remote_path}[/green]")

            except Exception as e:
                console.print(f"[yellow]Transfer via {protocol.upper()} failed: {e}[/yellow]")

                # 🔄 Fallback: try the other protocol
                fallback = "smb" if protocol == "sftp" else "sftp"
                console.print(f"[cyan]Trying fallback protocol: {fallback.upper()}[/cyan]")

                try:
                    remote_path = file_utils.remote_transfer(
                        config["source"],
                        config["destination"],
                        config["ip"],
                        config["username"],
                        config["password"],
                        fallback,
                    )
                    console.print(f"[green]File transferred via fallback {fallback.upper()} → {remote_path}[/green]")
                except Exception as e2:
                    console.print(f"[red]Transfer failed with both protocols: {e2}[/red]")

        else:
            console.print("[red]Invalid transfer mode[/red]")

    except Exception as e:
        console.print(f"[red]Transfer failed: {e}[/red]")


@file_transfer.command("receive")
@click.option("--save-dir", default=".", help="Directory to save incoming files")
@click.option("--port", default=5001, help="Port to listen on (default: 5001)")
def receive(save_dir, port):
    """Start a receiver for network transfers"""
    try:
        filepath = file_utils.receive_file_network(save_dir, port)
        console.print(f"[green]File received successfully → {filepath}[/green]")
    except Exception as e:
        console.print(f"[red]Receive failed: {e}[/red]")


@file_transfer.command("show-config")
def show_config():
    """Show current transfer configuration"""
    config = file_utils.load_config()
    if not config:
        console.print("[yellow]No transfer configuration found.[/yellow]")
    else:
        console.print("[cyan]Current transfer setup:[/cyan]")
        for k, v in config.items():
            console.print(f" - {k}: {v if v else '-'}")


@file_transfer.command("reset")
def reset_config():
    """Clear saved transfer configuration"""
    from pathlib import Path

    if file_utils.CONFIG_FILE.exists():
        file_utils.CONFIG_FILE.unlink()
        console.print("[green]Transfer configuration reset.[/green]")
    else:
        console.print("[yellow]No configuration to reset.[/yellow]")
