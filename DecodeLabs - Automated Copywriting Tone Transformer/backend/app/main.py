"""
FastAPI entry point for Lexora.

Includes generation, bulk CSV, backend-only account persistence and workspace
storage. The browser stores no permanent Lexora data.
"""
from __future__ import annotations

import csv
import io
import logging
import re
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Callable

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from app import db
from app.bulk_pipeline import CSVValidationError, parse_csv, run_bulk_job
from app.config import get_settings
from app.gemini_client import GeminiPermanentError, GeminiTransientError, generate_copy
from app.models import (
    PLATFORM_CONSTRAINTS,
    CTAType,
    ContentObjective,
    CopyLength,
    EmojiLevel,
    FormalityLevel,
    BulkResult,
    GenerationRequest,
    GenerationResponse,
    Platform,
    Tone,
    TransformMode,
)
from app.prompt_engine import compile_master_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lexora_api")
settings = get_settings()
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_login_buckets: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(
    title="Lexora AI Tone Studio",
    description="Gemini-powered copywriting and tone transformation engine",
    version="2.1.0",
)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str
    terms: bool = False


class SignInRequest(BaseModel):
    email: str
    password: str
    remember: bool = True


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    token: str
    new_password: str


class ProfileUpdateRequest(BaseModel):
    name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class WorkspaceItemRequest(BaseModel):
    item: dict[str, Any]


def validate_email(email: str) -> str:
    clean = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", clean):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    return clean


def validate_password(password: str) -> None:
    if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters and include one uppercase letter and one number.")


def session_cookie(response: Response, session_id: str, remember: bool = True) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * (30 if remember else 1),
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")


def current_user_optional(request: Request) -> dict[str, Any] | None:
    return db.get_user_for_session(request.cookies.get(settings.session_cookie_name))


def current_user(request: Request) -> dict[str, Any]:
    user = current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    return user


@app.on_event("startup")
async def startup() -> None:
    db.configure(settings.database_path, settings.upload_dir)


@app.middleware("http")
async def request_guard(request: Request, call_next: Callable):
    client = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _rate_buckets[client]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "Too many requests. Please wait a minute and try again."})
    bucket.append(now)

    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_request_bytes:
        return JSONResponse(status_code=413, content={"detail": "Request is too large. Please reduce the input size."})
    return await call_next(request)


@app.exception_handler(ValidationError)
async def validation_exception_handler(_: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": "Request validation failed.", "errors": exc.errors()})


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "lexora", "version": app.version}


@app.get("/api/meta")
async def meta() -> dict:
    return {
        "platforms": [
            {
                "value": p.value,
                "label": c["label"],
                "max_chars": c["max_chars"],
                "supports_hashtags": c["supports_hashtags"],
                "format": c["format"],
            }
            for p, c in PLATFORM_CONSTRAINTS.items()
        ],
        "tones": [t.value for t in Tone],
        "objectives": [item.value for item in ContentObjective],
        "copy_lengths": [item.value for item in CopyLength],
        "emoji_levels": [item.value for item in EmojiLevel],
        "formality_levels": [item.value for item in FormalityLevel],
        "cta_types": [item.value for item in CTAType],
        "transform_modes": [item.value for item in TransformMode],
        "variation_presets": ["Safe", "Creative", "Bold"],
        "bulk_max_rows": 200,
    }


@app.post("/api/auth/signup")
async def auth_signup(payload: SignUpRequest, response: Response) -> dict:
    email = validate_email(payload.email)
    validate_password(payload.password)
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Please enter your full name.")
    if not payload.terms:
        raise HTTPException(status_code=400, detail="Please agree to Lexora workspace terms.")
    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = db.create_user(payload.name, email, payload.password)
    sid = db.create_session(user["id"], remember=True)
    session_cookie(response, sid, remember=True)
    return {"user": user}


@app.post("/api/auth/signin")
async def auth_signin(payload: SignInRequest, response: Response, request: Request) -> dict:
    client = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _login_buckets[client]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= 12:
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Please wait and try again.")
    bucket.append(now)

    email = validate_email(payload.email)
    row = db.get_user_by_email(email)
    if not row or not db.verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    user = db.public_user(row)
    sid = db.create_session(user["id"], remember=payload.remember)
    session_cookie(response, sid, remember=payload.remember)
    return {"user": user}


@app.get("/api/auth/me")
async def auth_me(request: Request) -> dict:
    return {"user": current_user_optional(request)}


@app.post("/api/auth/logout")
async def auth_logout(request: Request, response: Response) -> dict:
    db.delete_session(request.cookies.get(settings.session_cookie_name))
    clear_session_cookie(response)
    return {"ok": True}


@app.post("/api/auth/forgot")
async def auth_forgot(payload: ForgotPasswordRequest) -> dict:
    email = validate_email(payload.email)
    token = db.create_reset_token(email)
    # No email provider is configured in this local build, so the backend returns
    # the one-time token for testing. In production, send this by email instead.
    return {
        "message": "If that account exists, a reset token has been prepared.",
        "reset_token": token or "",
    }


@app.post("/api/auth/reset")
async def auth_reset(payload: ResetPasswordRequest) -> dict:
    email = validate_email(payload.email)
    validate_password(payload.new_password)
    if not db.reset_password(email, payload.token.strip(), payload.new_password):
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired.")
    return {"ok": True, "message": "Password reset completed. Please sign in again."}


@app.patch("/api/profile")
async def profile_update(payload: ProfileUpdateRequest, user: dict = Depends(current_user)) -> dict:
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Please enter a valid full name.")
    return {"user": db.update_profile(user["id"], name=payload.name)}


@app.post("/api/profile/photo")
async def profile_photo(file: UploadFile = File(...), user: dict = Depends(current_user)) -> dict:
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Please upload JPG, PNG or WebP only.")
    raw = await file.read()
    if len(raw) > 1_500_000:
        raise HTTPException(status_code=413, detail="Profile image must be under 1.5 MB.")
    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    filename = f"profile_{user['id']}_{int(time.time())}{suffix}"
    path = Path(settings.upload_dir) / filename
    path.write_bytes(raw)
    updated = db.update_profile(user["id"], avatar_path=str(path))
    return {"user": updated}


@app.delete("/api/profile/photo")
async def profile_photo_delete(user: dict = Depends(current_user)) -> dict:
    return {"user": db.update_profile(user["id"], avatar_path="")}


@app.post("/api/profile/password")
async def profile_password(payload: ChangePasswordRequest, request: Request, response: Response, user: dict = Depends(current_user)) -> dict:
    validate_password(payload.new_password)
    if not db.change_password(user["id"], payload.current_password, payload.new_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    db.delete_session(request.cookies.get(settings.session_cookie_name))
    clear_session_cookie(response)
    return {"ok": True, "message": "Password changed. Please sign in again."}


@app.delete("/api/profile")
async def profile_delete(request: Request, response: Response, user: dict = Depends(current_user)) -> dict:
    db.delete_user(user["id"])
    db.delete_session(request.cookies.get(settings.session_cookie_name))
    clear_session_cookie(response)
    return {"ok": True}


@app.get("/api/workspace")
async def workspace(user: dict = Depends(current_user)) -> dict:
    return db.list_workspace(user["id"])


@app.post("/api/workspace/history")
async def workspace_history(payload: WorkspaceItemRequest, user: dict = Depends(current_user)) -> dict:
    return {"item": db.insert_workspace_item(user["id"], "history", payload.item, 80)}


@app.post("/api/workspace/favourites")
async def workspace_favourites(payload: WorkspaceItemRequest, user: dict = Depends(current_user)) -> dict:
    return {"item": db.insert_workspace_item(user["id"], "favourites", payload.item, 80)}


@app.post("/api/workspace/templates")
async def workspace_templates(payload: WorkspaceItemRequest, user: dict = Depends(current_user)) -> dict:
    return {"item": db.insert_workspace_item(user["id"], "templates", payload.item, 40)}


@app.delete("/api/workspace/{table}/{item_id}")
async def workspace_delete(table: str, item_id: str, user: dict = Depends(current_user)) -> dict:
    if table not in {"history", "favourites", "templates"}:
        raise HTTPException(status_code=404, detail="Workspace section not found.")
    db.delete_workspace_item(user["id"], table, item_id)
    return {"ok": True}


@app.delete("/api/workspace/{table}")
async def workspace_clear(table: str, user: dict = Depends(current_user)) -> dict:
    if table not in {"history", "favourites", "templates"}:
        raise HTTPException(status_code=404, detail="Workspace section not found.")
    db.clear_workspace_table(user["id"], table)
    return {"ok": True}


@app.post("/api/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest) -> GenerationResponse:
    prompt = compile_master_template(request)
    try:
        copy = await generate_copy(prompt, request.temperature, request.top_p)
    except GeminiPermanentError as exc:
        logger.error("Permanent Gemini error: %s", exc)
        raise HTTPException(status_code=400, detail=f"Gemini configuration error: {exc}") from exc
    except GeminiTransientError as exc:
        logger.warning("Transient Gemini error: %s", exc)
        raise HTTPException(status_code=502, detail=f"Generation failed after temporary retries: {exc}") from exc
    return GenerationResponse.build(request, copy)


@app.post("/api/bulk/generate", response_model=list[BulkResult])
async def bulk_generate(file: UploadFile = File(...)) -> list[BulkResult]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")
    raw_bytes = await file.read()
    if len(raw_bytes) > settings.max_bulk_file_bytes:
        raise HTTPException(status_code=413, detail="CSV is too large. Please upload a file under 2 MB.")
    try:
        rows = parse_csv(raw_bytes)
    except CSVValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not rows:
        raise HTTPException(status_code=400, detail="CSV contained no usable rows.")
    if len(rows) > 200:
        raise HTTPException(status_code=400, detail="Max 200 rows per bulk job.")
    return await run_bulk_job(rows)


@app.get("/api/bulk/template")
async def bulk_template() -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "product_name",
        "product_description",
        "target_audience",
        "content_objective",
        "language",
        "copy_length",
        "keywords",
        "brand_voice",
        "emoji_level",
        "number_of_variations",
        "formality_level",
        "cta_type",
        "platform",
        "tone",
        "temperature",
        "top_p",
    ])
    writer.writerow([
        "Aurora Wireless Earbuds",
        "Noise-cancelling earbuds with 30-hour battery life and IPX5 water resistance",
        "University students",
        ContentObjective.SALES.value,
        "English",
        CopyLength.MEDIUM.value,
        "wireless, battery, study, commute",
        "Energetic but premium. Avoid cheap-sounding hype.",
        EmojiLevel.LOW.value,
        "3",
        FormalityLevel.BALANCED.value,
        CTAType.SHOP_NOW.value,
        Platform.INSTAGRAM.value,
        Tone.ENERGETIC.value,
        "0.8",
        "0.9",
    ])
    writer.writerow([
        "FlowState Project Manager",
        "A project management SaaS tool built for distributed engineering teams",
        "Startup founders and engineering leads",
        ContentObjective.LEAD_GENERATION.value,
        "English",
        CopyLength.SHORT.value,
        "remote teams, roadmap, deadlines",
        "Clear, serious, B2B SaaS voice.",
        EmojiLevel.NONE.value,
        "3",
        FormalityLevel.FORMAL.value,
        CTAType.BOOK_DEMO.value,
        Platform.LINKEDIN.value,
        Tone.PROFESSIONAL.value,
        "0.4",
        "0.9",
    ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=lexora_bulk_template.csv"},
    )
