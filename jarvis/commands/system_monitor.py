import time
import psutil
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.progress import BarColumn, TextColumn, Progress
from rich.layout import Layout
from rich.panel import Panel

console = Console()


@click.group()
def system_monitor():
    """Monitor system resources in real-time"""
    pass


def make_progress_bar(label: str, value: float, total: float, unit: str) -> Progress:
    """Helper to create a progress bar"""
    return Progress(
        TextColumn(f"[bold]{label}[/bold]", justify="right"),
        BarColumn(bar_width=40),
        TextColumn(f"{value:.1f}/{total:.1f} {unit}" if total else f"{value:.1f} {unit}"),
        expand=True,
    )


@system_monitor.command("live")
@click.option("--interval", default=1, help="Refresh interval in seconds")
def live_monitor(interval):
    """Display live system monitor (CPU, Memory, Disk, Network)"""
    with Live(refresh_per_second=4, console=console, screen=True) as live:
        while True:
            layout = Layout()

            # CPU
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_bar = make_progress_bar("CPU %", cpu_percent, 100, "%")
            cpu_bar.add_task("", total=100, completed=cpu_percent)

            # Memory
            mem = psutil.virtual_memory()
            mem_bar = make_progress_bar("Memory", mem.used / (1024**3), mem.total / (1024**3), "GB")
            mem_bar.add_task("", total=mem.total, completed=mem.used)

            # Disk
            disk = psutil.disk_usage("/")
            disk_bar = make_progress_bar("Disk", disk.used / (1024**3), disk.total / (1024**3), "GB")
            disk_bar.add_task("", total=disk.total, completed=disk.used)

            # Network
            net = psutil.net_io_counters()
            net_table = Table(title="Network I/O", show_header=True, header_style="bold magenta")
            net_table.add_column("Sent (MB)", justify="right")
            net_table.add_column("Received (MB)", justify="right")
            net_table.add_row(f"{net.bytes_sent / (1024**2):.2f}", f"{net.bytes_recv / (1024**2):.2f}")

            # Layout
            layout.split_column(
                Layout(Panel(cpu_bar, title="CPU", border_style="cyan")),
                Layout(Panel(mem_bar, title="Memory", border_style="magenta")),
                Layout(Panel(disk_bar, title="Disk", border_style="green")),
                Layout(Panel(net_table, title="Network", border_style="yellow")),
            )

            live.update(layout)
            time.sleep(interval)
