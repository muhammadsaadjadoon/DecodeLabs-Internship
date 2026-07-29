from __future__ import annotations

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import random
import re
import secrets
import sqlite3
import time
import uuid
import shutil
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Literal

import requests
from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field, EmailStr, model_validator
from quality_pipeline import (
    AESTHETIC_THRESHOLD,
    SEMANTIC_THRESHOLD,
    QA_ENFORCE,
    extract_asset_from_json_file,
    moderate_input_text,
    run_visual_quality_review,
    should_reject_for_output_safety,
    should_reject_for_quality,
    stream_response_to_temp,
    validate_and_normalize_image,
)

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "change-this-dev-secret")
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "storage/prismora.db"))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = ROOT / DATABASE_PATH
STORAGE = ROOT / "storage"
IMAGES_DIR = STORAGE / "images"
AVATARS_DIR = STORAGE / "avatars"
TEMP_DIR = STORAGE / "tmp"
STATIC_DIR = ROOT / "static"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
CF_MODEL = os.getenv("CLOUDFLARE_MODEL", "@cf/black-forest-labs/flux-1-schnell").strip()
ALLOW_DEV_PLACEHOLDER = os.getenv("ALLOW_DEV_PLACEHOLDER", "false").lower() == "true"
QA_REGENERATION_ATTEMPTS = max(0, min(2, int(os.getenv("QA_REGENERATION_ATTEMPTS", "1"))))

for folder in [STORAGE, IMAGES_DIR, AVATARS_DIR, TEMP_DIR, STATIC_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Prismora", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

RATIO_MAP = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:5": (1024, 1280),
    "5:4": (1280, 1024),
    "3:4": (960, 1280),
    "4:3": (1280, 960),
    "21:9": (1536, 640),
}
MODE_HINTS = {
    "realistic": "photorealistic, real camera capture, natural skin/material texture, believable depth of field, no artificial look",
    "natural": "natural daylight, organic colors, authentic environment, subtle contrast, realistic imperfections",
    "cinematic": "cinematic lighting, dramatic composition, premium film still, controlled shadows, high dynamic range",
    "product": "premium product photography, clean commercial set, refined reflections, crisp edges, advertising quality",
    "portrait": "professional portrait, expressive face, realistic eyes, soft background separation, studio-quality lighting",
    "fantasy": "high-end fantasy art, luminous atmosphere, intricate details, majestic scale, polished concept art",
    "minimal": "minimal design, elegant negative space, restrained palette, premium editorial composition",
    "illustration": "high-quality illustration, clean forms, stylized details, refined visual storytelling",
}
STYLE_HINTS = {
    "premium": "luxury premium finish, precise details, balanced composition",
    "editorial": "editorial magazine style, sophisticated visual direction",
    "commercial": "high-end commercial campaign styling, polished brand presentation",
    "film": "cinematic film grade, lens character, atmospheric depth",
    "studio": "controlled studio lighting, polished professional output",
    "raw": "direct faithful rendering with minimal styling",
}

# -------------------------- database --------------------------
@contextmanager
def db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              email TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              avatar_path TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions(
              token_hash TEXT PRIMARY KEY,
              user_id INTEGER NOT NULL,
              created_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS settings(
              user_id INTEGER PRIMARY KEY,
              theme TEXT NOT NULL DEFAULT 'dark',
              default_mode TEXT NOT NULL DEFAULT 'realistic',
              default_ratio TEXT NOT NULL DEFAULT '1:1',
              default_style TEXT NOT NULL DEFAULT 'premium',
              auto_enhance INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS threads(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS messages(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              thread_id INTEGER NOT NULL,
              user_id INTEGER NOT NULL,
              role TEXT NOT NULL,
              content TEXT NOT NULL,
              generation_id INTEGER,
              created_at TEXT NOT NULL,
              FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS generations(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              thread_id INTEGER NOT NULL,
              prompt TEXT NOT NULL,
              enhanced_prompt TEXT,
              negative_prompt TEXT,
              mode TEXT NOT NULL,
              style TEXT NOT NULL,
              aspect_ratio TEXT NOT NULL,
              width INTEGER NOT NULL,
              height INTEGER NOT NULL,
              count INTEGER NOT NULL,
              seed INTEGER,
              provider TEXT NOT NULL,
              model TEXT NOT NULL,
              status TEXT NOT NULL,
              error_message TEXT,
              favorite INTEGER NOT NULL DEFAULT 0,
              safety_status TEXT NOT NULL DEFAULT 'pending',
              quality_status TEXT NOT NULL DEFAULT 'pending',
              qa_attempts INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
              FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS images(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              generation_id INTEGER NOT NULL,
              user_id INTEGER NOT NULL,
              file_path TEXT NOT NULL,
              mime_type TEXT NOT NULL,
              width INTEGER,
              height INTEGER,
              requested_width INTEGER,
              requested_height INTEGER,
              source_width INTEGER,
              source_height INTEGER,
              dimension_match INTEGER NOT NULL DEFAULT 1,
              dimension_adjusted INTEGER NOT NULL DEFAULT 0,
              dimension_warning TEXT,
              aesthetic_score REAL,
              semantic_score REAL,
              qa_passed INTEGER,
              qa_method TEXT,
              qa_notes TEXT,
              moderation_status TEXT NOT NULL DEFAULT 'not_checked',
              moderation_reason TEXT,
              sha256 TEXT NOT NULL,
              size_bytes INTEGER NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(generation_id) REFERENCES generations(id) ON DELETE CASCADE,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

init_db()

def ensure_column(conn: sqlite3.Connection, table: str, name: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if name not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

def migrate_quality_schema() -> None:
    with db() as conn:
        for name, definition in {
            "safety_status": "TEXT NOT NULL DEFAULT 'pending'",
            "quality_status": "TEXT NOT NULL DEFAULT 'pending'",
            "qa_attempts": "INTEGER NOT NULL DEFAULT 0",
        }.items():
            ensure_column(conn, "generations", name, definition)
        for name, definition in {
            "requested_width": "INTEGER",
            "requested_height": "INTEGER",
            "source_width": "INTEGER",
            "source_height": "INTEGER",
            "dimension_match": "INTEGER NOT NULL DEFAULT 1",
            "dimension_adjusted": "INTEGER NOT NULL DEFAULT 0",
            "dimension_warning": "TEXT",
            "aesthetic_score": "REAL",
            "semantic_score": "REAL",
            "qa_passed": "INTEGER",
            "qa_method": "TEXT",
            "qa_notes": "TEXT",
            "moderation_status": "TEXT NOT NULL DEFAULT 'not_checked'",
            "moderation_reason": "TEXT",
        }.items():
            ensure_column(conn, "images", name, definition)

migrate_quality_schema()

def user_columns(conn: sqlite3.Connection) -> set[str]:
    return {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}

def make_user_uid() -> str:
    return "USR-" + uuid.uuid4().hex[:12].upper()

# -------------------------- security --------------------------
def hash_password(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Choose a password with at least 8 characters.")
    salt = secrets.token_bytes(16)
    rounds = 250_000
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return f"pbkdf2_sha256${rounds}${base64.b64encode(salt).decode()}${base64.b64encode(key).decode()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, rounds, salt_b64, key_b64 = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(key_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def make_session(user_id: int, response: Response) -> None:
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(days=14)
    with db() as conn:
        conn.execute("INSERT INTO sessions(token_hash,user_id,created_at,expires_at) VALUES(?,?,?,?)", (token_hash, user_id, now_iso(), expires.isoformat()))
    response.set_cookie(
        "prismora_session",
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=14 * 24 * 60 * 60,
        path="/",
    )

def get_current_user(prismora_session: Optional[str] = Cookie(default=None)) -> sqlite3.Row:
    if not prismora_session:
        raise HTTPException(status_code=401, detail="Sign in to access your Prismora studio.")
    token_hash = hashlib.sha256(prismora_session.encode()).hexdigest()
    with db() as conn:
        row = conn.execute(
            """SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id
               WHERE sessions.token_hash=? AND sessions.expires_at>?""",
            (token_hash, now_iso()),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Your session has ended. Please sign in again.")
    return row

def require_user(user: sqlite3.Row = Depends(get_current_user)) -> sqlite3.Row:
    return user

def public_user(row: sqlite3.Row) -> dict[str, Any]:
    keys = set(row.keys())
    avatar_url = f"/api/profile/avatar/{row['id']}?v={int(time.time())}" if ("avatar_path" in keys and row["avatar_path"]) else None
    data = {"id": row["id"], "name": row["name"], "email": row["email"], "avatar_url": avatar_url, "created_at": row["created_at"] if "created_at" in keys else None}
    if "user_uid" in keys:
        data["user_uid"] = row["user_uid"]
    return data

# -------------------------- schemas --------------------------
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=120)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=120)

class ForgotPasswordIn(BaseModel):
    email: EmailStr

ThemeName = Literal["dark", "light"]
ModeName = Literal["realistic", "natural", "cinematic", "product", "portrait", "fantasy", "minimal", "illustration"]
StyleName = Literal["premium", "editorial", "commercial", "film", "studio", "raw"]
AspectRatioName = Literal["1:1", "16:9", "9:16", "4:5", "5:4", "3:4", "4:3", "21:9"]
ResolutionName = Literal["auto", "1024x1024", "1344x768", "768x1344", "1024x1280", "1280x1024", "960x1280", "1280x960", "1536x640"]

class SettingsIn(BaseModel):
    theme: ThemeName = "dark"
    default_mode: ModeName = "realistic"
    default_ratio: AspectRatioName = "1:1"
    default_style: StyleName = "premium"
    auto_enhance: bool = True

class EnhanceIn(BaseModel):
    prompt: str = Field(min_length=2, max_length=4000)
    mode: ModeName = "realistic"
    style: StyleName = "premium"
    aspect_ratio: AspectRatioName = "1:1"
    negative_prompt: str = Field(default="", max_length=2000)
    source_context: str = Field(default="", max_length=3000)

class GenerateIn(BaseModel):
    prompt: str = Field(min_length=2, max_length=4000)
    negative_prompt: str = Field(default="", max_length=2000)
    mode: ModeName = "realistic"
    style: StyleName = "premium"
    aspect_ratio: AspectRatioName = "1:1"
    resolution: ResolutionName = "auto"
    count: int = Field(default=1, ge=1, le=4)
    seed: Optional[int] = Field(default=None, ge=0, le=2_147_483_647)
    auto_enhance: bool = True
    thread_id: Optional[int] = Field(default=None, ge=1)
    refine_from_generation_id: Optional[int] = Field(default=None, ge=1)
    refine_instruction: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def validate_canvas(self) -> "GenerateIn":
        expected_width, expected_height = RATIO_MAP[self.aspect_ratio]
        expected_resolution = f"{expected_width}x{expected_height}"
        if self.resolution != "auto" and self.resolution != expected_resolution:
            raise ValueError(
                f"Resolution {self.resolution} is incompatible with aspect ratio {self.aspect_ratio}. "
                f"Use auto or {expected_resolution}."
            )
        return self

class ProfileIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr

class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=120)
    new_password: str = Field(min_length=8, max_length=120)

# -------------------------- helpers --------------------------
def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}

def sanitize_filename(name: str) -> str:
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    return "".join(ch for ch in name if ch in keep)[:90] or secrets.token_hex(8)

def resolve_size(aspect_ratio: AspectRatioName, resolution: ResolutionName = "auto") -> tuple[int, int]:
    expected = RATIO_MAP[aspect_ratio]
    if resolution == "auto":
        return expected
    width_text, height_text = resolution.split("x", 1)
    selected = (int(width_text), int(height_text))
    if selected != expected:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "CANVAS_VALIDATION_FAILED",
                "message": f"The selected resolution does not match the {aspect_ratio} canvas. Use {expected[0]}×{expected[1]}.",
            },
        )
    return selected

def clean_prompt_text(value: str, max_chars: int = 2048) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^```(?:text|markdown)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = re.sub(r"^(?:final|enhanced|image)\s+prompt\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:")
    return text

def final_prompt(
    prompt: str,
    mode: str,
    style: str,
    aspect_ratio: str,
    negative_prompt: str = "",
    source_context: str = "",
) -> str:
    idea = clean_prompt_text(prompt, 1200)
    mode_hint = MODE_HINTS.get(mode, MODE_HINTS["realistic"])
    style_hint = STYLE_HINTS.get(style, STYLE_HINTS["premium"])
    context = clean_prompt_text(source_context, 700)
    parts = [
        f"Create one coherent image of {idea}.",
        "Preserve the exact main subject, subject count, actions, relationships, colors, clothing, objects and setting stated by the user.",
        f"Visual direction: {mode_hint}; {style_hint}.",
        f"Composition: intentional {aspect_ratio} framing, clear focal hierarchy, accurate perspective, balanced depth and natural subject separation.",
        "Quality: realistic materials and textures, controlled professional lighting, clean anatomy, natural facial features and hands when visible, crisp meaningful detail, no unrelated additions.",
    ]
    if context:
        parts.insert(1, f"Refinement context: {context}. Apply only the requested changes and keep all unspecified details consistent.")
    avoid = clean_prompt_text(negative_prompt, 500) or "blurry output, malformed anatomy, duplicate subjects, extra limbs, distorted hands, unreadable text, watermark, logo artifacts, noisy details"
    parts.append(f"Avoid: {avoid}.")
    return clean_prompt_text(" ".join(parts), 2048)

def call_gemini_for_prompt(payload: EnhanceIn) -> str:
    fallback = final_prompt(
        payload.prompt,
        payload.mode,
        payload.style,
        payload.aspect_ratio,
        payload.negative_prompt,
        payload.source_context,
    )
    if not GEMINI_API_KEY:
        return fallback
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    refinement_rules = (
        "This is a refinement request. Treat the previous prompt as the locked base scene. Apply only the requested changes, "
        "preserve the same subject identity, subject count, composition and all unspecified details."
        if payload.source_context
        else "This is a new image request."
    )
    instruction = f"""
You are Prismora Prompt Architect, a precision prompt compiler for an AI image model. You are not a chatbot.

Understand prompts written in English, Urdu, Roman Urdu or Hindi and convert their meaning into fluent natural English.
Return one single production-ready image prompt only, with no markdown, headings, notes, explanations or quotation marks.

NON-NEGOTIABLE RULES:
- Preserve the user's exact intent: main subject, number of subjects, identity descriptors, action, relationships, emotions, colors, clothing, objects, location and requested atmosphere.
- Never replace a vague subject with an unrelated concept. Add only neutral visual detail that supports the user's idea.
- Keep the prompt focused and non-repetitive, ideally 90 to 170 words and under 1800 characters.
- Build a coherent scene with clear subject hierarchy, camera/framing, lighting, environment, materials, depth and realistic detail.
- Use natural anatomy and believable surfaces. Do not stuff the prompt with empty phrases such as repeated 8K, masterpiece or ultra quality.
- Do not include safety policy, provider names, diagnostics, negative-prompt headings or technical errors.
- {refinement_rules}

Selected visual mode: {payload.mode} — {MODE_HINTS.get(payload.mode, MODE_HINTS['realistic'])}
Selected style: {payload.style} — {STYLE_HINTS.get(payload.style, STYLE_HINTS['premium'])}
Target composition: {payload.aspect_ratio}
User negative preferences: {payload.negative_prompt or 'none'}
Previous/refinement context: {payload.source_context or 'none'}
User idea/base prompt: {payload.prompt}
""".strip()
    body = {
        "contents": [{"role": "user", "parts": [{"text": instruction}]}],
        "generationConfig": {
            "temperature": 0.25,
            "topP": 0.85,
            "maxOutputTokens": 900,
        },
    }
    try:
        r = requests.post(url, json=body, timeout=(3.05, 35))
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        cleaned = clean_prompt_text(text, 2048)
        return cleaned if len(cleaned) >= 20 else fallback
    except Exception:
        return fallback

def make_dev_placeholder_file(prompt: str, width: int, height: int) -> Path:
    path = TEMP_DIR / f"preview_{uuid.uuid4().hex}.png"
    im = Image.new("RGB", (width, height), (28, 27, 24))
    draw = ImageDraw.Draw(im)
    for y in range(height):
        c = int(25 + 50 * y / max(1, height))
        draw.line([(0, y), (width, y)], fill=(c, c - 2, c + 8))
    text = "Prismora Preview\nImage engine setup required\nto create live visuals"
    draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=34, outline=(222, 190, 120), width=3)
    draw.text((70, 80), text, fill=(245, 238, 220))
    brief = prompt[:180] + ("..." if len(prompt) > 180 else "")
    draw.text((70, 210), brief, fill=(205, 198, 180))
    im.save(path, format="PNG")
    return path

def friendly_generation_error(message: str) -> str:
    raw = str(message or '').strip()
    lowered = raw.lower()
    if any(term in lowered for term in ['nsfw', 'nude', 'nudity', 'sexual', 'adult content', 'explicit', 'unsafe', 'offensive']):
        return 'Prismora is designed for respectful, safe visual creation and cannot produce explicit, adult, offensive, or harmful content. Please revise your prompt.'
    if 'quality assurance' in lowered or 'semantic alignment' in lowered or 'aesthetic threshold' in lowered:
        return 'The visual did not meet Prismora quality standards after an automatic retry. Please refine the prompt and try again.'
    if 'dimension' in lowered and ('rejected' in lowered or 'not accepted' in lowered):
        return 'The selected canvas could not be processed by the image engine. Choose a supported Prismora format and try again.'
    if 'cloudflare token/account permission failed' in lowered:
        return 'The image engine is not currently available. Please review the service configuration and try again.'
    if 'timed out after retries' in lowered:
        return 'The image took longer than expected to create. Please try again in a moment.'
    if lowered.startswith('cloudflare request failed:'):
        return 'Prismora could not complete this creation. Please refine the prompt or try again shortly.'
    if any(term in lowered for term in ['backend', 'database', 'cloudflare', 'api error', 'exception', 'traceback', 'connectionerror', 'runtimeerror', 'internal server']):
        return 'Prismora encountered a temporary service issue. Please try again shortly.'
    return raw

def _response_excerpt(response: requests.Response, limit: int = 500) -> str:
    try:
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=256):
            if not chunk:
                continue
            take = chunk[: max(0, limit - total)]
            chunks.append(take)
            total += len(take)
            if total >= limit:
                break
        return b"".join(chunks).decode("utf-8", errors="replace")
    except Exception:
        return ""

def call_cloudflare_flux(prompt: str, width: int, height: int, seed: Optional[int]) -> Path:
    if not CF_ACCOUNT_ID or not CF_TOKEN:
        if ALLOW_DEV_PLACEHOLDER:
            return make_dev_placeholder_file(prompt, width, height)
        raise HTTPException(status_code=503, detail="The image engine is not yet configured. Complete the service setup and restart Prismora.")
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_MODEL}"
    provider_prompt = clean_prompt_text(prompt, 2048)
    provider_payload: dict[str, Any] = {
        "prompt": provider_prompt,
        "steps": 8,
        "width": width,
        "height": height,
    }
    if seed is not None:
        provider_payload["seed"] = seed
    headers = {"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"}
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with requests.post(
                url,
                headers=headers,
                json=provider_payload,
                stream=True,
                timeout=(3.05, 90),
            ) as response:
                if response.status_code in (429, 500, 502, 503, 504):
                    excerpt = _response_excerpt(response, 180)
                    last_error = RuntimeError(f"Temporary image engine error {response.status_code}: {excerpt}")
                    time.sleep((2 ** attempt) + random.random())
                    continue
                if response.status_code in (401, 403):
                    raise HTTPException(status_code=401, detail="The image service could not be authorized. Review the service credentials and permissions.")
                if response.status_code in (400, 422):
                    excerpt = _response_excerpt(response, 500)
                    raise HTTPException(status_code=422, detail=friendly_generation_error(f"Dimension or safety request was not accepted: {excerpt}"))
                if response.status_code >= 400:
                    excerpt = _response_excerpt(response, 500)
                    raise HTTPException(status_code=400, detail=friendly_generation_error(f"Cloudflare request failed: {excerpt}"))
                return stream_response_to_temp(response, TEMP_DIR)
        except HTTPException:
            raise
        except requests.Timeout as exc:
            last_error = exc
            time.sleep((2 ** attempt) + random.random())
        except requests.RequestException as exc:
            last_error = exc
            time.sleep((2 ** attempt) + random.random())
    raise HTTPException(status_code=504, detail="The image engine took longer than expected. Please try again in a moment.")

def commit_validated_image(user_id: int, generation_id: int, candidate: Any, report: Any) -> dict[str, Any]:
    fname = f"u{user_id}_g{generation_id}_{candidate.sha256[:12]}{candidate.extension}"
    final_path = IMAGES_DIR / fname
    shutil.move(str(candidate.temp_path), final_path)
    return {
        "file_path": f"storage/images/{fname}",
        "mime_type": candidate.mime_type,
        "width": candidate.width,
        "height": candidate.height,
        "requested_width": candidate.requested_width,
        "requested_height": candidate.requested_height,
        "source_width": candidate.source_width,
        "source_height": candidate.source_height,
        "dimension_match": int(candidate.dimension_match),
        "dimension_adjusted": int(candidate.dimension_adjusted),
        "dimension_warning": candidate.dimension_warning,
        "aesthetic_score": report.aesthetic_score,
        "semantic_score": report.semantic_score,
        "qa_passed": None if report.passed is None else int(report.passed),
        "qa_method": report.method,
        "qa_notes": report.notes,
        "moderation_status": report.safety_status,
        "moderation_reason": report.safety_reason,
        "sha256": candidate.sha256,
        "size_bytes": candidate.size_bytes,
        "url": f"/api/images/{fname}",
    }

def ensure_thread(user_id: int, thread_id: Optional[int], title: str) -> int:
    with db() as conn:
        if thread_id:
            row = conn.execute("SELECT id FROM threads WHERE id=? AND user_id=?", (thread_id, user_id)).fetchone()
            if row:
                return int(row["id"])
        cur = conn.execute(
            "INSERT INTO threads(user_id,title,created_at,updated_at) VALUES(?,?,?,?)",
            (user_id, title[:70] or "Untitled generation", now_iso(), now_iso()),
        )
        return int(cur.lastrowid)

def serialize_generation(gen: sqlite3.Row) -> dict[str, Any]:
    with db() as conn:
        imgs = conn.execute("SELECT * FROM images WHERE generation_id=? ORDER BY id", (gen["id"],)).fetchall()
    d = row_to_dict(gen)
    d["favorite"] = bool(d.get("favorite"))
    serialized_images = []
    for img in imgs:
        item = row_to_dict(img)
        item["dimension_match"] = bool(item.get("dimension_match"))
        item["dimension_adjusted"] = bool(item.get("dimension_adjusted"))
        if item.get("qa_passed") is not None:
            item["qa_passed"] = bool(item["qa_passed"])
        item["url"] = f"/api/images/{Path(img['file_path']).name}"
        serialized_images.append(item)
    d["images"] = serialized_images
    return d

# -------------------------- routes --------------------------
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "app": "Prismora",
        "database": DATABASE_PATH.exists(),
        "gemini_configured": bool(GEMINI_API_KEY),
        "cloudflare_configured": bool(CF_ACCOUNT_ID and CF_TOKEN),
        "quality_assurance": {
            "enabled": True,
            "enforced": QA_ENFORCE,
            "aesthetic_threshold": AESTHETIC_THRESHOLD,
            "semantic_threshold": SEMANTIC_THRESHOLD,
            "automatic_retries": QA_REGENERATION_ATTEMPTS,
        },
        "storage": str(STORAGE),
    }

@app.post("/api/auth/register")
def register(data: RegisterIn, response: Response):
    with db() as conn:
        exists = conn.execute("SELECT id FROM users WHERE lower(email)=lower(?)", (str(data.email),)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="An account is already associated with this email.")
        columns = user_columns(conn)
        insert_cols = ["name", "email", "password_hash", "created_at"]
        insert_vals = [data.name.strip(), str(data.email).lower(), hash_password(data.password), now_iso()]
        # Compatibility for old Prismora databases that already have a NOT NULL user_uid column.
        # SQLite CREATE TABLE IF NOT EXISTS keeps the old schema, so registration must provide it.
        if "user_uid" in columns:
            insert_cols.insert(0, "user_uid")
            insert_vals.insert(0, make_user_uid())
        placeholders = ",".join(["?"] * len(insert_cols))
        cur = conn.execute(
            f"INSERT INTO users({','.join(insert_cols)}) VALUES({placeholders})",
            tuple(insert_vals),
        )
        user_id = int(cur.lastrowid)
        conn.execute("INSERT INTO settings(user_id) VALUES(?)", (user_id,))
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    make_session(user_id, response)
    return {"user": public_user(row)}

@app.post("/api/auth/login")
def login(data: LoginIn, response: Response):
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email)=lower(?)", (str(data.email),)).fetchone()
    if not row or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="The email or password you entered is incorrect.")
    make_session(int(row["id"]), response)
    return {"user": public_user(row)}

@app.post("/api/auth/forgot-password")
def forgot_password(data: ForgotPasswordIn):
    # Safe generic response: do not reveal whether an email exists.
    # Production deployments can connect this endpoint to email delivery or admin reset workflow.
    with db() as conn:
        row = conn.execute("SELECT id FROM users WHERE lower(email)=lower(?)", (str(data.email),)).fetchone()
        if row:
            conn.execute(
                "INSERT INTO messages(thread_id,user_id,role,content,created_at) VALUES(?,?,?,?,?)",
                (ensure_thread(int(row["id"]), None, "Account recovery"), int(row["id"]), "system", "Password recovery requested from Prismora sign-in screen.", now_iso()),
            )
    return {"ok": True, "message": "If an account is associated with this email, recovery instructions are ready."}

@app.post("/api/auth/logout")
def logout(response: Response, prismora_session: Optional[str] = Cookie(default=None)):
    if prismora_session:
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(prismora_session.encode()).hexdigest(),))
    response.delete_cookie("prismora_session", path="/")
    return {"ok": True}

@app.get("/api/auth/me")
def me(user: sqlite3.Row = Depends(require_user)):
    return {"user": public_user(user)}

@app.get("/api/settings")
def get_settings(user: sqlite3.Row = Depends(require_user)):
    with db() as conn:
        row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user["id"],)).fetchone()
        if not row:
            conn.execute("INSERT INTO settings(user_id) VALUES(?)", (user["id"],))
            row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user["id"],)).fetchone()
    d = row_to_dict(row)
    d["auto_enhance"] = bool(d["auto_enhance"])
    return d

@app.put("/api/settings")
def put_settings(data: SettingsIn, user: sqlite3.Row = Depends(require_user)):
    if data.default_ratio not in RATIO_MAP:
        raise HTTPException(status_code=400, detail="Select a supported canvas format.")
    with db() as conn:
        conn.execute(
            """INSERT INTO settings(user_id,theme,default_mode,default_ratio,default_style,auto_enhance)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET theme=excluded.theme,default_mode=excluded.default_mode,default_ratio=excluded.default_ratio,default_style=excluded.default_style,auto_enhance=excluded.auto_enhance""",
            (user["id"], data.theme, data.default_mode, data.default_ratio, data.default_style, int(data.auto_enhance)),
        )
    return get_settings(user)

@app.put("/api/profile")
def update_profile(data: ProfileIn, user: sqlite3.Row = Depends(require_user)):
    with db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE lower(email)=lower(?) AND id<>?", (str(data.email), user["id"])).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="This email is already associated with another account.")
        conn.execute("UPDATE users SET name=?, email=? WHERE id=?", (data.name.strip(), str(data.email).lower(), user["id"]))
        row = conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
    return {"user": public_user(row)}

@app.put("/api/profile/password")
def change_profile_password(data: ChangePasswordIn, user: sqlite3.Row = Depends(require_user)):
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="The current password you entered is incorrect.")
    new_hash = hash_password(data.new_password)
    with db() as conn:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user["id"]))
    return {"ok": True}

@app.post("/api/profile/avatar")
def upload_avatar(file: UploadFile = File(...), user: sqlite3.Row = Depends(require_user)):
    raw = file.file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Your profile portrait must be smaller than 5 MB.")
    try:
        im = Image.open(BytesIO(raw)).convert("RGB")
        im.thumbnail((512, 512), Image.Resampling.LANCZOS)
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=90)
        data = buf.getvalue()
    except Exception:
        raise HTTPException(status_code=400, detail="Choose a valid image file for your profile portrait.")
    fname = f"avatar_u{user['id']}_{secrets.token_hex(8)}.jpg"
    path = AVATARS_DIR / fname
    path.write_bytes(data)
    with db() as conn:
        old = conn.execute("SELECT avatar_path FROM users WHERE id=?", (user["id"],)).fetchone()
        conn.execute("UPDATE users SET avatar_path=? WHERE id=?", (f"storage/avatars/{fname}", user["id"]))
    return {"avatar_url": f"/api/profile/avatar/{user['id']}?v={int(time.time())}"}

@app.get("/api/profile/avatar/{user_id}")
def avatar(user_id: int):
    with db() as conn:
        row = conn.execute("SELECT avatar_path FROM users WHERE id=?", (user_id,)).fetchone()
    if not row or not row["avatar_path"]:
        raise HTTPException(status_code=404, detail="No profile portrait is available.")
    path = ROOT / row["avatar_path"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="The profile portrait is currently unavailable.")
    return FileResponse(path, media_type="image/jpeg")

def safety_error_detail(code: str, message: str, categories: Optional[list[str]] = None) -> dict[str, Any]:
    return {"code": code, "message": message, "categories": categories or []}

def cleanup_generation_assets(generation_id: int) -> None:
    with db() as conn:
        rows = conn.execute("SELECT file_path FROM images WHERE generation_id=?", (generation_id,)).fetchall()
        conn.execute("DELETE FROM images WHERE generation_id=?", (generation_id,))
    for row in rows:
        try:
            (ROOT / row["file_path"]).unlink(missing_ok=True)
        except Exception:
            pass

@app.post("/api/prompt/enhance")
def enhance(data: EnhanceIn, user: sqlite3.Row = Depends(require_user)):
    decision = moderate_input_text(data.prompt)
    if not decision.allowed:
        raise HTTPException(
            status_code=422,
            detail=safety_error_detail(decision.code, decision.message, decision.categories),
        )
    enhanced = call_gemini_for_prompt(data)
    enhanced_decision = moderate_input_text(enhanced)
    if not enhanced_decision.allowed:
        raise HTTPException(
            status_code=422,
            detail=safety_error_detail("ENHANCED_PROMPT_SAFETY_REJECTED", enhanced_decision.message, enhanced_decision.categories),
        )
    return {"enhanced_prompt": enhanced}

@app.post("/api/generations")
def generate(data: GenerateIn, user: sqlite3.Row = Depends(require_user)):
    width, height = resolve_size(data.aspect_ratio, data.resolution)
    safety_text = " ".join(part for part in [data.prompt, data.refine_instruction] if part).strip()
    input_decision = moderate_input_text(safety_text)
    if not input_decision.allowed:
        raise HTTPException(
            status_code=422,
            detail=safety_error_detail(input_decision.code, input_decision.message, input_decision.categories),
        )

    context = ""
    prompt_for_model = data.prompt.strip()
    record_prompt = data.prompt.strip()
    message_content = data.prompt.strip()
    thread_hint = data.thread_id

    if data.refine_from_generation_id:
        with db() as conn:
            prev = conn.execute(
                "SELECT * FROM generations WHERE id=? AND user_id=?",
                (data.refine_from_generation_id, user["id"]),
            ).fetchone()
        if not prev:
            raise HTTPException(status_code=404, detail="The original creation is no longer available for refinement.")
        instruction = data.refine_instruction.strip()
        if not instruction:
            raise HTTPException(status_code=400, detail="Add a clear refinement direction before continuing.")
        source_prompt = (prev["enhanced_prompt"] or prev["prompt"] or data.prompt).strip()
        prompt_for_model = source_prompt
        record_prompt = f"Refine: {instruction}"
        message_content = instruction
        thread_hint = data.thread_id or int(prev["thread_id"])
        context = (
            f"Previous complete visual prompt: {source_prompt}. "
            f"Requested refinement: {instruction}. "
            "Return the complete revised prompt, preserve every unspecified detail, and do not redesign the scene."
        )

    enh_payload = EnhanceIn(
        prompt=prompt_for_model,
        mode=data.mode,
        style=data.style,
        aspect_ratio=data.aspect_ratio,
        negative_prompt=data.negative_prompt,
        source_context=context,
    )
    enhanced = (
        call_gemini_for_prompt(enh_payload)
        if data.auto_enhance
        else final_prompt(
            prompt_for_model,
            data.mode,
            data.style,
            data.aspect_ratio,
            data.negative_prompt,
            context,
        )
    )
    enhanced = clean_prompt_text(enhanced, 2048)
    enhanced_decision = moderate_input_text(enhanced)
    if not enhanced_decision.allowed:
        raise HTTPException(
            status_code=422,
            detail=safety_error_detail("ENHANCED_PROMPT_SAFETY_REJECTED", enhanced_decision.message, enhanced_decision.categories),
        )

    thread_id = ensure_thread(user["id"], thread_hint, record_prompt)
    with db() as conn:
        conn.execute("UPDATE threads SET updated_at=? WHERE id=?", (now_iso(), thread_id))
        conn.execute(
            "INSERT INTO messages(thread_id,user_id,role,content,created_at) VALUES(?,?,?,?,?)",
            (thread_id, user["id"], "user", message_content, now_iso()),
        )
        cur = conn.execute(
            """INSERT INTO generations(
                   user_id,thread_id,prompt,enhanced_prompt,negative_prompt,mode,style,aspect_ratio,
                   width,height,count,seed,provider,model,status,safety_status,quality_status,qa_attempts,created_at
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                user["id"], thread_id, record_prompt, enhanced, data.negative_prompt, data.mode, data.style,
                data.aspect_ratio, width, height, data.count, data.seed, "cloudflare-workers-ai", CF_MODEL,
                "processing", "input_passed", "pending", 0, now_iso(),
            ),
        )
        generation_id = int(cur.lastrowid)

    total_qa_attempts = 0
    accepted_reports: list[Any] = []
    try:
        for idx in range(data.count):
            seed = data.seed + idx if data.seed is not None else None
            accepted_meta: Optional[dict[str, Any]] = None
            for qa_attempt in range(QA_REGENERATION_ATTEMPTS + 1):
                total_qa_attempts += 1
                review_prompt = enhanced
                if qa_attempt:
                    review_prompt = (
                        f"{enhanced} Improve exact prompt fidelity, composition coherence, natural anatomy, lighting and material quality. "
                        "Do not change the requested subject, count, action or setting."
                    )
                provider_file = call_cloudflare_flux(review_prompt, width, height, seed)
                candidate = validate_and_normalize_image(provider_file, width, height, TEMP_DIR)
                report = run_visual_quality_review(candidate.temp_path, enhanced, GEMINI_API_KEY, GEMINI_MODEL)

                if should_reject_for_output_safety(report):
                    candidate.temp_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=422,
                        detail=safety_error_detail(
                            "OUTPUT_SAFETY_REJECTED",
                            "Prismora's visual safety review rejected the generated result. Please revise the prompt.",
                            [report.safety_reason] if report.safety_reason else [],
                        ),
                    )

                if should_reject_for_quality(report):
                    candidate.temp_path.unlink(missing_ok=True)
                    if qa_attempt < QA_REGENERATION_ATTEMPTS:
                        continue
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "code": "QUALITY_ASSURANCE_FAILED",
                            "message": (
                                "The visual did not meet Prismora's automated quality threshold after regeneration. "
                                "Please add clearer subject, action, scene or style detail and try again."
                            ),
                            "quality": {
                                "aesthetic_score": report.aesthetic_score,
                                "semantic_score": report.semantic_score,
                                "aesthetic_threshold": AESTHETIC_THRESHOLD,
                                "semantic_threshold": SEMANTIC_THRESHOLD,
                            },
                        },
                    )

                accepted_meta = commit_validated_image(user["id"], generation_id, candidate, report)
                accepted_reports.append(report)
                break

            if accepted_meta is None:
                raise RuntimeError("Automated quality assurance did not produce an acceptable visual.")

            with db() as conn:
                cur = conn.execute(
                    """INSERT INTO images(
                           generation_id,user_id,file_path,mime_type,width,height,requested_width,requested_height,
                           source_width,source_height,dimension_match,dimension_adjusted,dimension_warning,
                           aesthetic_score,semantic_score,qa_passed,qa_method,qa_notes,moderation_status,moderation_reason,
                           sha256,size_bytes,created_at
                       ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        generation_id, user["id"], accepted_meta["file_path"], accepted_meta["mime_type"],
                        accepted_meta["width"], accepted_meta["height"], accepted_meta["requested_width"],
                        accepted_meta["requested_height"], accepted_meta["source_width"], accepted_meta["source_height"],
                        accepted_meta["dimension_match"], accepted_meta["dimension_adjusted"], accepted_meta["dimension_warning"],
                        accepted_meta["aesthetic_score"], accepted_meta["semantic_score"], accepted_meta["qa_passed"],
                        accepted_meta["qa_method"], accepted_meta["qa_notes"], accepted_meta["moderation_status"],
                        accepted_meta["moderation_reason"], accepted_meta["sha256"], accepted_meta["size_bytes"], now_iso(),
                    ),
                )
                accepted_meta["id"] = int(cur.lastrowid)

        quality_status = "passed"
        if any(report.passed is None for report in accepted_reports):
            quality_status = "review_unavailable"
        safety_status = "passed"
        if any(report.safe is None for report in accepted_reports):
            safety_status = "output_review_unavailable"
        with db() as conn:
            conn.execute(
                "UPDATE generations SET status='completed', safety_status=?, quality_status=?, qa_attempts=? WHERE id=?",
                (safety_status, quality_status, total_qa_attempts, generation_id),
            )
            conn.execute(
                "INSERT INTO messages(thread_id,user_id,role,content,generation_id,created_at) VALUES(?,?,?,?,?,?)",
                (thread_id, user["id"], "assistant", "Visual creation completed and validated.", generation_id, now_iso()),
            )
            gen = conn.execute("SELECT * FROM generations WHERE id=?", (generation_id,)).fetchone()
        return serialize_generation(gen)
    except HTTPException as exc:
        cleanup_generation_assets(generation_id)
        detail = exc.detail
        message = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        friendly = friendly_generation_error(message)
        safety_status = "rejected" if isinstance(detail, dict) and "SAFETY" in str(detail.get("code", "")) else "failed"
        quality_status = "rejected" if isinstance(detail, dict) and detail.get("code") == "QUALITY_ASSURANCE_FAILED" else "failed"
        with db() as conn:
            conn.execute(
                "UPDATE generations SET status='failed', error_message=?, safety_status=?, quality_status=?, qa_attempts=? WHERE id=?",
                (friendly, safety_status, quality_status, total_qa_attempts, generation_id),
            )
        if isinstance(detail, dict):
            raise HTTPException(status_code=exc.status_code, detail={**detail, "message": friendly})
        raise HTTPException(status_code=exc.status_code, detail=friendly)
    except Exception as exc:
        cleanup_generation_assets(generation_id)
        friendly = friendly_generation_error(str(exc))
        with db() as conn:
            conn.execute(
                "UPDATE generations SET status='failed', error_message=?, safety_status='failed', quality_status='failed', qa_attempts=? WHERE id=?",
                (friendly, total_qa_attempts, generation_id),
            )
        raise HTTPException(status_code=500, detail=friendly)

@app.get("/api/generations")
def list_generations(user: sqlite3.Row = Depends(require_user), favorite: Optional[int] = None):
    with db() as conn:
        if favorite is None:
            rows = conn.execute("SELECT * FROM generations WHERE user_id=? ORDER BY id DESC LIMIT 120", (user["id"],)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM generations WHERE user_id=? AND favorite=? ORDER BY id DESC LIMIT 120", (user["id"], int(favorite))).fetchall()
    return {"items": [serialize_generation(r) for r in rows]}

@app.get("/api/threads")
def list_threads(user: sqlite3.Row = Depends(require_user)):
    with db() as conn:
        rows = conn.execute("SELECT * FROM threads WHERE user_id=? ORDER BY updated_at DESC LIMIT 80", (user["id"],)).fetchall()
    return {"items": [row_to_dict(r) for r in rows]}

@app.get("/api/threads/{thread_id}")
def get_thread(thread_id: int, user: sqlite3.Row = Depends(require_user)):
    with db() as conn:
        thread = conn.execute("SELECT * FROM threads WHERE id=? AND user_id=?", (thread_id, user["id"])).fetchone()
        if not thread:
            raise HTTPException(status_code=404, detail="This creation session is no longer available.")
        messages = conn.execute("SELECT * FROM messages WHERE thread_id=? AND user_id=? ORDER BY id", (thread_id, user["id"])).fetchall()
        gens = conn.execute("SELECT * FROM generations WHERE thread_id=? AND user_id=? ORDER BY id", (thread_id, user["id"])).fetchall()
    return {"thread": row_to_dict(thread), "messages": [row_to_dict(m) for m in messages], "generations": [serialize_generation(g) for g in gens]}

@app.post("/api/generations/{generation_id}/favorite")
def toggle_favorite(generation_id: int, user: sqlite3.Row = Depends(require_user)):
    with db() as conn:
        row = conn.execute("SELECT favorite FROM generations WHERE id=? AND user_id=?", (generation_id, user["id"])).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="This creation is no longer available.")
        new = 0 if row["favorite"] else 1
        conn.execute("UPDATE generations SET favorite=? WHERE id=?", (new, generation_id))
    return {"favorite": bool(new)}

@app.delete("/api/generations/{generation_id}")
def delete_generation(generation_id: int, user: sqlite3.Row = Depends(require_user)):
    with db() as conn:
        gen = conn.execute("SELECT id FROM generations WHERE id=? AND user_id=?", (generation_id, user["id"])).fetchone()
        if not gen:
            raise HTTPException(status_code=404, detail="This creation is no longer available.")
        imgs = conn.execute("SELECT file_path FROM images WHERE generation_id=?", (generation_id,)).fetchall()
        conn.execute("DELETE FROM generations WHERE id=?", (generation_id,))
    for img in imgs:
        path = ROOT / img["file_path"]
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
    return {"ok": True}

@app.get("/api/images/{filename}")
def get_image(filename: str, user: sqlite3.Row = Depends(require_user)):
    safe = sanitize_filename(Path(filename).stem) + Path(filename).suffix
    path = IMAGES_DIR / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="This visual is no longer available.")
    with db() as conn:
        row = conn.execute("SELECT id FROM images WHERE file_path=? AND user_id=?", (f"storage/images/{safe}", user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="You do not have access to this visual.")
    return FileResponse(path)

@app.get("/{path:path}")
def spa_fallback(path: str):
    candidate = STATIC_DIR / path
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(STATIC_DIR / "index.html")
