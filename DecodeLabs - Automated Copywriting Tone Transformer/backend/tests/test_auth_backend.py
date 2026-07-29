import sqlite3

from fastapi.testclient import TestClient


def test_signup_login_logout_backend_session(tmp_path, monkeypatch):
    db_file = tmp_path / "lexora_auth.sqlite3"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))

    from app.config import get_settings

    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as client:
        payload = {
            "name": "Lexora User",
            "email": "lexora@example.com",
            "password": "Password1",
            "terms": True,
        }
        created = client.post("/api/auth/signup", json=payload)
        assert created.status_code == 200
        assert created.json()["user"]["email"] == "lexora@example.com"

        logged_out = client.post("/api/auth/logout")
        assert logged_out.status_code == 200
        assert client.get("/api/auth/me").json()["user"] is None

        bad = client.post(
            "/api/auth/signin",
            json={"email": "lexora@example.com", "password": "WrongPass1"},
        )
        assert bad.status_code == 401

        good = client.post(
            "/api/auth/signin",
            json={
                "email": "lexora@example.com",
                "password": "Password1",
                "remember": True,
            },
        )
        assert good.status_code == 200
        assert client.get("/api/auth/me").json()["user"]["email"] == "lexora@example.com"

    with sqlite3.connect(db_file) as connection:
        row = connection.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            ("lexora@example.com",),
        ).fetchone()

    assert row and row[0] != "Password1"
    assert row[0].startswith("pbkdf2_sha256$260000$")
