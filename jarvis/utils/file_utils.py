import os
import shutil
import socket
import json
from pathlib import Path

import paramiko   # for SFTP
import smbprotocol  # for SMB (Windows shares)

CONFIG_FILE = Path.home() / ".jarvis" / "file_transfer.json"
BUFFER_SIZE = 4096


# ----------------- CONFIG MANAGEMENT ----------------- #

def save_config(config: dict):
    """Save transfer config to ~/.jarvis/file_transfer.json"""
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


def load_config():
    """Load saved transfer config"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None


def setup_transfer(mode, source, destination=None, ip=None, username=None, password=None, protocol="sftp"):
    """Store a transfer setup configuration"""
    config = {
        "mode": mode,            # local | network | remote
        "protocol": protocol,    # sftp | smb
        "source": source,
        "destination": destination,
        "ip": ip,
        "username": username,
        "password": password,
    }
    save_config(config)
    return config


# ----------------- LOCAL TRANSFER ----------------- #

def local_transfer(source, destination):
    """Copy file/folder on the same machine"""
    if os.path.isdir(source):
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)
    return True


# ----------------- NETWORK TRANSFER ----------------- #

def send_file_network(source, ip, port=5001):
    """Send a file to another machine over LAN"""
    filesize = os.path.getsize(source)
    s = socket.socket()
    s.connect((ip, port))
    s.send(f"{os.path.basename(source)}:{filesize}".encode())

    with open(source, "rb") as f:
        while True:
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                break
            s.sendall(bytes_read)

    s.close()
    return True


def receive_file_network(destination_dir=".", port=5001):
    """Receive a file over LAN"""
    s = socket.socket()
    s.bind(("", port))
    s.listen(1)
    client_socket, addr = s.accept()

    received = client_socket.recv(BUFFER_SIZE).decode()
    filename, filesize = received.split(":")
    filesize = int(filesize)
    filepath = os.path.join(destination_dir, filename)

    with open(filepath, "wb") as f:
        bytes_received = 0
        while bytes_received < filesize:
            bytes_read = client_socket.recv(BUFFER_SIZE)
            if not bytes_read:
                break
            f.write(bytes_read)
            bytes_received += len(bytes_read)

    client_socket.close()
    s.close()
    return filepath


# ----------------- REMOTE TRANSFER ----------------- #

def remote_transfer(source, destination, ip, username, password, protocol="sftp"):
    """
    Transfer file to remote system using SFTP (default) or SMB.
    """
    if protocol == "sftp":
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)

        sftp = ssh.open_sftp()
        try:
            sftp.stat(destination)
        except FileNotFoundError:
            # Create destination folder if missing
            sftp.mkdir(destination)

        remote_path = os.path.join(destination, os.path.basename(source))
        sftp.put(source, remote_path)

        sftp.close()
        ssh.close()
        return remote_path

    elif protocol == "smb":
        # SMB setup
        try:
            smbprotocol.ClientConfig(username=username, password=password)
        except Exception as e:
            raise RuntimeError(f"SMB authentication failed: {e}")

        # Destination should be in format: SHARE/folder
        if "/" in destination:
            share, path = destination.split("/", 1)
        else:
            share, path = destination, ""

        remote_path = f"\\\\{ip}\\{share}\\{path}\\{os.path.basename(source)}"

        try:
            with open(source, "rb") as src_file, open(remote_path, "wb") as dst_file:
                shutil.copyfileobj(src_file, dst_file)
        except Exception as e:
            raise RuntimeError(f"SMB transfer failed: {e}")

        return remote_path

    else:
        raise ValueError("Unsupported protocol. Use 'sftp' or 'smb'.")


# ----------------- PROTOCOL DETECTION ----------------- #

def detect_protocol(ip: str) -> str:
    """Detect protocol by checking open ports on remote system."""
    try:
        # Check port 22 (SSH/SFTP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex((ip, 22)) == 0:
            s.close()
            return "sftp"
        s.close()
    except Exception:
        pass

    try:
        # Check port 445 (SMB)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex((ip, 445)) == 0:
            s.close()
            return "smb"
        s.close()
    except Exception:
        pass

    return None
