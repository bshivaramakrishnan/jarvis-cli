Jarvis – Your Development Assistant CLI:

Jarvis is a cross-platform command-line assistant that bundles essential developer tools into one CLI. It supports Git branch management, system monitoring, file transfers, commit helpers (AI-powered), database exploration, and more.
This document covers everything:
Requirements & setup (Windows, macOS, Linux)
Installation instructions
Environment variables (OpenAI API, file transfer config, DB config)
Full feature list
Command reference for each module
Usage examples

REQUIREMENTS:

Jarvis requires Python 3.8+ and has been tested on:
macOS (Intel & Apple Silicon, zsh/bash shell)
Linux (Ubuntu, Arch, Debian)
Windows 10/11 (PowerShell, CMD, WSL2)

Install Python:
macOS: 
Python 3 is usually preinstalled. To upgrade:
brew install python3

Linux (Debian/Ubuntu):
sudo apt update
sudo apt install python3 python3-venv python3-pip -y

Windows:
Download from https://www.python.org/downloads/windows/
During installation, tick "Add to PATH"

SETUP & INSTALLATION:

Clone the Repository:
git clone https://github.com/bshivaramakrishnan/jarvis-cli.git
cd jarvis-cli

Create a Virtual Environment:

On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

On Windows (PowerShell):
python -m venv venv
venv\Scripts\activate

Install Dependencies:
pip install -e .
Alternatively, install from requirements file:
pip install -r requirements.txt

ENVIRONMENT VARIABLES : 
OpenAI API Key
Jarvis uses OpenAI for AI-powered commit messages.
Get your key from https://platform.openai.com/api-keys If you have a project-scoped key (sk-proj-...), also note your project ID.

Save the key permanently:
On macOS/Linux:
nano ~/.zshrc
export OPENAI_API_KEY="sk-your-key-here"
export OPENAI_PROJECT="proj-xxxx" (optional)
source ~/.zshrc

On Windows (PowerShell):
setx OPENAI_API_KEY "sk-your-key-here"
setx OPENAI_PROJECT "proj-xxxx"

Verify it is set:
macOS/Linux: echo $OPENAI_API_KEY
Windows: echo $env:OPENAI_API_KEY

FEATURES:

Jarvis provides the following modules:

Git Branch Manager:
Add branch metadata (branch name, commit hash, issue ID, description)
List branches and their statuses
Update branch status (open, merged, closed)

File Transfer:
Local: Copy files within the same machine
Network: Transfer files across machines on LAN
Remote: Transfer files to remote machines via SFTP or SMB
Configurable once, reusable via transfer command
Handles credentials (username/password) when required
Port Checker
Check which process is using a specific port
Process Killer
Search processes by name or port
Kill processes safely
System Monitor
Real-time dashboard (like a mini htop)
Shows CPU, memory, disk, and network usage
Updates live in terminal
Commit Helper
AI-powered commit message generator
Falls back to rule-based commit messages if AI unavailable
Supports Conventional Commit format
Database Explorer
Supports SQLite and Postgres
Save DB connection config once
List tables
Run SQL queries
Search keywords across text columns
Export results as CSV or JSON
Diagnostics
Run checks for all modules
Extended mode verifies configs and connectivity

CLI COMMANDS & USAGE:

GENERAL:
jarvis hello
jarvis diagnostics

GIT MANAGER:
jarvis git-manager add-branch
jarvis git-manager list-branches
jarvis git-manager update-status <branch_id> <status>

FILE TRANSFER Setup config:
jarvis file-transfer setup --mode local --source ./data.txt --destination ./backup/
jarvis file-transfer setup --mode network --source ./data.txt --ip 192.168.1.5
jarvis file-transfer setup --mode remote --source ./data.txt --destination /remote/path/ --ip 192.168.1.10 --username user --password pass

Transfer files:
jarvis file-transfer transfer
Receive files (for network mode):
jarvis file-transfer receive --save-dir ./incoming --port 5001

Config management:
jarvis file-transfer show-config
jarvis file-transfer reset

PORT CHECKER:
jarvis port-checker check --port 8080

PROCESS KILLER:
jarvis process-killer search-name chrome
jarvis process-killer kill-name chrome
jarvis process-killer kill-port 5000

SYSTEM MONITOR:
jarvis system-monitor live

COMMIT HELPER:
jarvis commit-helper generate
jarvis commit-helper generate --show-diff
jarvis commit-helper generate --commit
jarvis commit-helper generate --all
jarvis commit-helper generate --scope cli

DATABASE EXPLORER Connect:
jarvis db-explorer connect --db sqlite --path ./data.db
jarvis db-explorer connect --db postgres --host localhost --port 5432 --user myuser --password mypass --dbname mydb
Tables:
jarvis db-explorer tables

Query:
jarvis db-explorer query "SELECT * FROM users LIMIT 5;"
jarvis db-explorer query "SELECT * FROM sales;" --export csv --out sales.csv
Search:
jarvis db-explorer search "john_doe"
Config management:
jarvis db-explorer show-config
jarvis db-explorer reset

FILE TRANSFER MODES:

Local Mode:
Source and destination are paths on the same machine Example: jarvis file-transfer setup --mode local --source ./data.txt --destination ./backup/

Network Mode:
Requires source, target IP, and receiver running Sender:
jarvis file-transfer setup --mode network --source ./data.txt --ip 192.168.1.25
jarvis file-transfer transfer Receiver:
jarvis file-transfer receive --save-dir ./incoming

Remote Mode:
Supports SFTP (port 22) and SMB (port 445)
Requires username and password Example:
jarvis file-transfer setup --mode remote --source ./data.txt --destination /home/user/backup --ip 192.168.1.50 --username admin --password secret
jarvis file-transfer transfer

DEVELOPMENT & INSTALLATION NOTES:

Install locally in development mode:
pip install -e .
After installation, the jarvis command is available globally in your shell.
All configuration files (file-transfer, DB) are stored under:
~/.jarvis/

Dependencies are pinned in requirements.txt. To install:
pip install -r requirements.txt

Jarvis is packaged using pyproject.toml and setuptools. To build and distribute:
pip install build twine
python -m build
twine upload dist/*

AUTHOR
Shivaramakrishnan B Software Engineer | Systems Developer
