import os
import psutil
import platform
import signal

def search_process_by_name(name: str):
    """Find processes by name (case-insensitive)."""
    results = []
    for proc in psutil.process_iter(attrs=["pid", "name", "username", "status"]):
        try:
            if name and name.lower() in proc.info["name"].lower():
                results.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return results

def search_process_by_port(port: int):
    """Find the process using a given port."""
    matches = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr and conn.laddr.port == port:
            pid = conn.pid
            if pid is None:
                continue
            try:
                proc = psutil.Process(pid)
                matches.append({
                    "pid": pid,
                    "name": proc.name(),
                    "user": proc.username(),
                    "status": proc.status()
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                matches.append({
                    "pid": pid,
                    "name": "Unknown",
                    "user": "N/A",
                    "status": "N/A"
                })
    return matches

def kill_process(pid: int) -> bool:
    """Kill a process by PID (cross-platform)."""
    try:
        if platform.system() == "Windows":
            os.system(f"taskkill /F /PID {pid} >nul 2>&1")
        else:
            os.kill(pid, signal.SIGKILL)
        return True
    except Exception:
        return False
    
def get_system_stats():
    """Return current CPU, memory, disk, and network stats."""
    stats = {
        "cpu": psutil.cpu_percent(interval=0.5),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "net_sent": round(psutil.net_io_counters().bytes_sent / (1024 * 1024), 2),
        "net_recv": round(psutil.net_io_counters().bytes_recv / (1024 * 1024), 2),
    }
    return stats