import os
import json
import sqlite3
import csv
import json as _json
from pathlib import Path
from typing import Tuple, List, Optional, Any

CONFIG_PATH = Path.home() / ".jarvis" / "db_config.json"


# ----------------- config management ----------------- #

def save_db_config(config: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        _json.dump(config, f, indent=2)
    return config


def load_db_config() -> Optional[dict]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return _json.load(f)
    return None


def clear_db_config():
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
        return True
    return False


# ----------------- connection helpers ----------------- #

def _get_sqlite_conn(path: str):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _get_postgres_conn(host: str, port: int, user: str, password: str, dbname: str):
    try:
        import psycopg2
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
        return conn
    except Exception as e:
        raise RuntimeError(f"Failed to import/connect to Postgres: {e}")


def get_connection(config: Optional[dict] = None):
    """
    Returns a DB connection object according to config.
    config example:
      { "type":"sqlite", "path":"./data.db" }
      { "type":"postgres","host":"localhost","port":5432,"user":"u","password":"p","dbname":"db" }
    """
    cfg = config or load_db_config()
    if not cfg:
        raise RuntimeError("No DB config found. Run connect first.")
    if cfg["type"] == "sqlite":
        return _get_sqlite_conn(cfg["path"])
    elif cfg["type"] == "postgres":
        return _get_postgres_conn(cfg["host"], int(cfg.get("port", 5432)), cfg["user"], cfg["password"], cfg["dbname"])
    else:
        raise ValueError("Unsupported db type")


# ----------------- utility functions ----------------- #

def list_tables(config: Optional[dict] = None) -> List[str]:
    conn = get_connection(config)
    try:
        cfg = config or load_db_config()
        if cfg["type"] == "sqlite":
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
            return [row["name"] for row in cur.fetchall()]
        else:  # postgres
            cur = conn.cursor()
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type='BASE TABLE'
                ORDER BY table_name;
            """)
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def run_query(sql: str, config: Optional[dict] = None, fetch_limit: Optional[int] = 500) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """
    Run a query. Returns (columns, rows). If it's not a SELECT, returns ([], []) and executes DML.
    """
    conn = get_connection(config)
    try:
        cfg = config or load_db_config()
        cur = conn.cursor()
        cur.execute(sql)
        # decide if results
        if cur.description:
            cols = [col[0] for col in cur.description]
            rows = cur.fetchmany(fetch_limit) if fetch_limit else cur.fetchall()
            return cols, rows
        else:
            # DML statement executed
            conn.commit()
            return [], []
    finally:
        conn.close()


def _sqlite_text_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = []
    for row in cur.fetchall():
        name = row["name"] if isinstance(row, sqlite3.Row) else row[1]
        coltype = row["type"] if isinstance(row, sqlite3.Row) else row[2]
        if coltype and any(t in coltype.upper() for t in ("CHAR", "CLOB", "TEXT")):
            cols.append(name)
    return cols


def _postgres_text_columns(conn, table: str) -> List[str]:
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s;
    """, (table,))
    cols = []
    for name, data_type in cur.fetchall():
        if data_type and any(t in data_type for t in ("character varying", "text", "varchar", "char")):
            cols.append(name)
    return cols


def search_keyword(keyword: str, config: Optional[dict] = None, limit_per_table: int = 50) -> dict:
    """
    Search keyword across textual columns in all tables.
    Returns dict { table_name: (columns, rows) } for matches (rows limited).
    """
    cfg = config or load_db_config()
    conn = get_connection(config)
    results = {}
    keyword_like = f"%{keyword}%"
    try:
        tables = list_tables(config)
        for t in tables:
            text_cols = []
            if cfg["type"] == "sqlite":
                text_cols = _sqlite_text_columns(conn, t)
                placeholder = "?"
            else:
                text_cols = _postgres_text_columns(conn, t)
                placeholder = "%s"

            if not text_cols:
                continue

            where_clauses = " OR ".join([f"{col} LIKE {placeholder}" for col in text_cols])
            sql = f"SELECT * FROM {t} WHERE {where_clauses} LIMIT {limit_per_table};"
            params = [keyword_like] * len(text_cols)
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                cols = [d[0] for d in cur.description]
                results[t] = (cols, rows)
        return results
    finally:
        conn.close()


def export_results(columns: List[str], rows: List[tuple], outpath: str, format: str = "csv"):
    outpath = Path(outpath)
    if format == "csv":
        with open(outpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for r in rows:
                writer.writerow([_serialize_cell(c) for c in r])
    elif format == "json":
        arr = [dict(zip(columns, [_serialize_cell(c) for c in r])) for r in rows]
        with open(outpath, "w", encoding="utf-8") as f:
            _json.dump(arr, f, indent=2, default=str)
    else:
        raise ValueError("Unsupported export format; choose csv or json.")
    return outpath


def _serialize_cell(cell):
    if cell is None:
        return ""
    if isinstance(cell, (bytes, bytearray)):
        try:
            return cell.decode("utf-8", errors="replace")
        except Exception:
            return str(cell)
    return cell
