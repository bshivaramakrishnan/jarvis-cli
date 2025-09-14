import sqlite3

DB_NAME = "branches.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            commit_hash TEXT,
            issue_id TEXT,
            description TEXT,
            status TEXT DEFAULT 'open'
        )
    """)
    conn.commit()
    conn.close()

def add_branch(name, commit_hash, issue_id, description):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO branches (name, commit_hash, issue_id, description) VALUES (?, ?, ?, ?)",
        (name, commit_hash, issue_id, description)
    )
    conn.commit()
    conn.close()

def list_branches():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM branches")
    branches = c.fetchall()
    conn.close()
    return branches

def update_branch_status(branch_id, status):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE branches SET status = ? WHERE id = ?", (status, branch_id))
    conn.commit()
    conn.close()
    
def delete_branch(branch_id: int):
    """Delete a branch from DB by ID"""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM branches WHERE id = ?", (branch_id,))
    conn.commit()
    conn.close()
