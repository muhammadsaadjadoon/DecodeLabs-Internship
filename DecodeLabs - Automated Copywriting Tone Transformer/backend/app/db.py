"""SQLite persistence layer for Lexora.

The frontend must not store accounts, workspace, favourites, templates or profile
images in browser storage. This module keeps those records in the backend DB and
associates every private row with the authenticated session user.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

DB_PATH: Path | None = None
UPLOAD_DIR: Path | None = None


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def configure(db_path: str | Path, upload_dir: str | Path) -> None:
    global DB_PATH, UPLOAD_DIR
    DB_PATH = Path(db_path)
    UPLOAD_DIR = Path(upload_dir)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    if DB_PATH is None:
        raise RuntimeError("Database has not been configured.")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with connect() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              email TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              plan TEXT NOT NULL DEFAULT 'Lexora Starter',
              avatar_path TEXT DEFAULT '',
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS password_resets (
              token TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              used INTEGER NOT NULL DEFAULT 0,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS history (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              payload TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS favourites (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              payload TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS templates (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              payload TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return f"pbkdf2_sha256$260000${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_b64, digest_b64 = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def public_user(row: sqlite3.Row | dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    avatar_path = data.get("avatar_path") or ""
    return {
        "id": data["id"],
        "name": data["name"],
        "email": data["email"],
        "plan": data.get("plan") or "Lexora Starter",
        "created_at": data["created_at"],
        "avatar_url": f"/uploads/{Path(avatar_path).name}" if avatar_path else "",
    }


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with connect() as con:
        return con.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()


def get_user_by_id(user_id: str) -> sqlite3.Row | None:
    with connect() as con:
        return con.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(name: str, email: str, password: str) -> dict[str, Any]:
    user_id = secrets.token_urlsafe(18)
    now = utcnow()
    with connect() as con:
        con.execute(
            "INSERT INTO users (id, name, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name.strip(), email.lower().strip(), hash_password(password), now),
        )
        row = con.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(row)  # type: ignore[return-value]


def create_session(user_id: str, remember: bool = True) -> str:
    session_id = secrets.token_urlsafe(36)
    ttl = timedelta(days=30 if remember else 1)
    with connect() as con:
        con.execute(
            "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, utcnow(), (datetime.now(timezone.utc) + ttl).isoformat()),
        )
    return session_id


def get_user_for_session(session_id: str | None) -> dict[str, Any] | None:
    if not session_id:
        return None
    with connect() as con:
        row = con.execute(
            """
            SELECT users.* FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.id = ? AND sessions.expires_at > ?
            """,
            (session_id, utcnow()),
        ).fetchone()
    return public_user(row)


def delete_session(session_id: str | None) -> None:
    if not session_id:
        return
    with connect() as con:
        con.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def update_profile(user_id: str, name: str | None = None, avatar_path: str | None = None) -> dict[str, Any]:
    with connect() as con:
        if name is not None:
            con.execute("UPDATE users SET name = ? WHERE id = ?", (name.strip(), user_id))
        if avatar_path is not None:
            con.execute("UPDATE users SET avatar_path = ? WHERE id = ?", (avatar_path, user_id))
        row = con.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(row)  # type: ignore[return-value]


def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    with connect() as con:
        row = con.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row or not verify_password(current_password, row["password_hash"]):
            return False
        con.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
        con.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    return True


def delete_user(user_id: str) -> None:
    with connect() as con:
        row = con.execute("SELECT avatar_path FROM users WHERE id = ?", (user_id,)).fetchone()
        con.execute("DELETE FROM users WHERE id = ?", (user_id,))
    if row and row["avatar_path"]:
        try:
            Path(row["avatar_path"]).unlink(missing_ok=True)
        except Exception:
            pass


def create_reset_token(email: str) -> str | None:
    row = get_user_by_email(email)
    if not row:
        return None
    token = secrets.token_urlsafe(24)
    with connect() as con:
        con.execute(
            "INSERT INTO password_resets (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, row["id"], utcnow(), (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()),
        )
    return token


def reset_password(email: str, token: str, new_password: str) -> bool:
    row = get_user_by_email(email)
    if not row:
        return False
    with connect() as con:
        reset = con.execute(
            "SELECT * FROM password_resets WHERE token = ? AND user_id = ? AND used = 0 AND expires_at > ?",
            (token, row["id"], utcnow()),
        ).fetchone()
        if not reset:
            return False
        con.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), row["id"]))
        con.execute("UPDATE password_resets SET used = 1 WHERE token = ?", (token,))
        con.execute("DELETE FROM sessions WHERE user_id = ?", (row["id"],))
    return True


def list_workspace(user_id: str) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    with connect() as con:
        for table in ("history", "favourites", "templates"):
            rows = con.execute(
                f"SELECT id, created_at, payload FROM {table} WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            items = []
            for row in rows:
                payload = json.loads(row["payload"])
                payload.setdefault("id", row["id"])
                payload.setdefault("created_at", row["created_at"])
                items.append(payload)
            output[table] = items
    return output


def insert_workspace_item(user_id: str, table: str, payload: dict[str, Any], limit: int) -> dict[str, Any]:
    if table not in {"history", "favourites", "templates"}:
        raise ValueError("Invalid workspace table")
    item_id = payload.get("id") or secrets.token_urlsafe(18)
    created_at = payload.get("created_at") or utcnow()
    payload = {**payload, "id": item_id, "created_at": created_at}
    with connect() as con:
        con.execute(
            f"INSERT INTO {table} (id, user_id, created_at, payload) VALUES (?, ?, ?, ?)",
            (item_id, user_id, created_at, json.dumps(payload, ensure_ascii=False)),
        )
        stale = con.execute(
            f"SELECT id FROM {table} WHERE user_id = ? ORDER BY created_at DESC LIMIT -1 OFFSET ?",
            (user_id, limit),
        ).fetchall()
        for row in stale:
            con.execute(f"DELETE FROM {table} WHERE id = ? AND user_id = ?", (row["id"], user_id))
    return payload


def delete_workspace_item(user_id: str, table: str, item_id: str) -> None:
    if table not in {"history", "favourites", "templates"}:
        raise ValueError("Invalid workspace table")
    with connect() as con:
        con.execute(f"DELETE FROM {table} WHERE id = ? AND user_id = ?", (item_id, user_id))


def clear_workspace_table(user_id: str, table: str) -> None:
    if table not in {"history", "favourites", "templates"}:
        raise ValueError("Invalid workspace table")
    with connect() as con:
        con.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
