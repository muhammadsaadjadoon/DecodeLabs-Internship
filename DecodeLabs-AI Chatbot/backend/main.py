from __future__ import annotations

import os
import traceback
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chat_store import ChatStore, clean_title

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "Oryn")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.1-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
BASE_SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are Oryn, a professional AI assistant by Zorex. Answer accurately, keep context from this chat, and format responses in a clean readable style.",
)

SYSTEM_PROMPT = (
    f"{BASE_SYSTEM_PROMPT.strip()}\n\n"
    "Response rules: Answer the user's exact request directly and naturally. "
    "Do not start every reply with a greeting or self-introduction. "
    "Do not say 'Hello, I am Oryn' unless the user is greeting you or asking who you are. "
    "Do not add 'About my creator', 'About my origin', background notes, company notes, or creator details unless the user explicitly asks who built you, who created you, about Zorex, or about Muhammad Saad Jadoon. "
    "For coding questions, provide the code and explanation only. "
    "Keep replies professional, useful, and human-like."
)
MAX_RESPONSE_TOKENS = int(os.getenv("MAX_RESPONSE_TOKENS", "1400"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "28"))
MAX_HISTORY_TOKENS = int(os.getenv("MAX_HISTORY_TOKENS", "10000"))
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes", "on"}

store = ChatStore(DATA_DIR / "chats.json")
app = FastAPI(title=f"{APP_NAME} AI Chatbot", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = None


class ChatCreate(BaseModel):
    title: str | None = Field(default=None, max_length=80)


class ChatPatch(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    pinned: bool | None = None


class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=30000)


class RegenerateRequest(BaseModel):
    message: str | None = Field(default=None, max_length=30000)


def get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        from google import genai

        _client = genai.Client(api_key=GEMINI_API_KEY, vertexai=False)
    return _client


def to_gemini_contents(messages) -> list[dict[str, Any]]:
    contents = []
    for message in messages:
        role = "model" if message.role == "assistant" else "user"
        text = message.content
        if message.role == "assistant":
            text = remove_unasked_identity_boilerplate(text, "")
        contents.append({"role": role, "parts": [{"text": text}]})
    return contents


def demo_reply(user_message: str) -> str:
    cleaned = clean_title(user_message, "your message")
    return (
        f"Message received: **{cleaned}**.\n\n"
        "The interface and backend are working. Add your `GEMINI_API_KEY` inside `backend/.env`, "
        "then restart the server to enable real AI replies with Gemini and saved chat history."
    )


def is_network_error(exc: Exception) -> bool:
    text = f"{exc.__class__.__name__} {exc}".lower()
    markers = (
        "connection", "connect", "network", "internet", "dns", "name resolution",
        "temporary failure", "timed out", "timeout", "unreachable", "getaddrinfo",
        "connection reset", "connection refused", "nodename", "no route",
    )
    return any(marker in text for marker in markers)


def public_model_error(exc: Exception) -> str:
    text = f"{exc.__class__.__name__} {exc}".lower()
    if is_network_error(exc):
        return "No internet connection. Oryn could not reach the AI service. Please connect to the internet and try again."
    if "api key" in text or "unauthorized" in text or "permission" in text or "authentication" in text:
        return "The AI service is not configured correctly. Please check the API key in backend/.env and restart the server."
    if "quota" in text or "rate" in text or "429" in text or "resource exhausted" in text:
        return "The AI service is temporarily busy or the usage limit has been reached. Please wait a moment and try again."
    if "safety" in text or "blocked" in text:
        return "Oryn could not safely complete that request. Please rephrase it and try again."
    return "Oryn could not complete this request right now. Please try again in a moment."


def user_asked_identity(text: str) -> bool:
    q = (text or "").lower()
    identity_terms = (
        "who are you", "who built", "who made", "who created", "creator", "created you",
        "built you", "made you", "about you", "your origin", "your background",
        "zorex", "zorel", "oryn", "saad", "muhammad saad", "jadoon",
    )
    return any(term in q for term in identity_terms)


def remove_unasked_identity_boilerplate(reply: str, latest_user_message: str) -> str:
    if user_asked_identity(latest_user_message):
        return reply.strip()

    lines = reply.splitlines()
    cleaned: list[str] = []
    skip_rest = False
    boilerplate_heads = (
        "about my creator", "about my creators", "about my origin", "about my background",
        "a quick note on my background", "quick note on my background", "my background",
        "about my creators:", "about my origin:",
    )

    for line in lines:
        normalized = line.strip().lower().strip("*#:- ")
        if any(normalized.startswith(head) for head in boilerplate_heads):
            skip_rest = True
            continue
        if skip_rest:
            # Drop the trailing creator/origin block.
            continue
        cleaned.append(line)

    result = "\n".join(cleaned).strip()
    intro_prefixes = (
        "Hello! I am Oryn, your AI assistant from Zorex. ",
        "Hello! I am Oryn, your helpful, modern AI assistant by Zorex. ",
        "Hello! I am Oryn, a clear, helpful, and modern AI assistant developed by Zorex. ",
        "Hello! I am Oryn, your clear and helpful AI assistant, brought to you by Zorex. ",
    )
    for prefix in intro_prefixes:
        if result.startswith(prefix):
            result = result[len(prefix):].lstrip()
    return result or reply.strip()


def call_model(chat_id: str) -> tuple[str, dict[str, Any]]:
    context_messages = store.model_context(
        chat_id,
        max_messages=MAX_HISTORY_MESSAGES,
        max_history_tokens=MAX_HISTORY_TOKENS,
    )
    if not context_messages:
        return "Tell me what you want to build or ask.", {}

    latest_user_message = context_messages[-1].content

    if not GEMINI_API_KEY:
        if DEMO_MODE:
            return demo_reply(context_messages[-1].content), {"demo_mode": True}
        raise HTTPException(status_code=503, detail="The AI service is not configured. Add GEMINI_API_KEY in backend/.env and restart the server.")

    try:
        client = get_client()
        from google.genai import types

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=to_gemini_contents(context_messages),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=MAX_RESPONSE_TOKENS,
                temperature=float(os.getenv("MODEL_TEMPERATURE", "0.7")),
            ),
        )
        reply = (getattr(response, "text", None) or "").strip()
        usage = getattr(response, "usage_metadata", None)
        usage_payload = {
            "input_tokens": getattr(usage, "prompt_token_count", None) if usage else None,
            "output_tokens": getattr(usage, "candidates_token_count", None) if usage else None,
            "total_tokens": getattr(usage, "total_token_count", None) if usage else None,
        }
        if not reply:
            reply = "I could not produce a response. Please try again."
        reply = remove_unasked_identity_boilerplate(reply, latest_user_message)
        return reply, usage_payload
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        status_code = 503 if is_network_error(exc) else 502
        raise HTTPException(status_code=status_code, detail=public_model_error(exc))


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "model": MODEL_NAME,
        "api_key_configured": bool(GEMINI_API_KEY),
        "demo_mode": DEMO_MODE and not bool(GEMINI_API_KEY),
    }


@app.get("/api/chats")
def list_chats():
    return {"chats": store.list_chats()}


@app.post("/api/chats")
def create_chat(payload: ChatCreate):
    chat = store.create_chat(payload.title)
    return store.client_payload(chat.id, MAX_HISTORY_TOKENS)


@app.get("/api/chats/{chat_id}")
def get_chat(chat_id: str):
    try:
        return store.client_payload(chat_id, MAX_HISTORY_TOKENS)
    except KeyError:
        raise HTTPException(status_code=404, detail="Chat not found.")


@app.patch("/api/chats/{chat_id}")
def update_chat(chat_id: str, payload: ChatPatch):
    try:
        chat = store.update_chat(chat_id, title=payload.title, pinned=payload.pinned)
        return store.client_payload(chat.id, MAX_HISTORY_TOKENS)
    except KeyError:
        raise HTTPException(status_code=404, detail="Chat not found.")


@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: str):
    if not store.delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found.")
    return {"deleted": True}


@app.post("/api/chats/{chat_id}/clear")
def clear_chat(chat_id: str):
    try:
        chat = store.clear_chat(chat_id)
        return store.client_payload(chat.id, MAX_HISTORY_TOKENS)
    except KeyError:
        raise HTTPException(status_code=404, detail="Chat not found.")


@app.post("/api/chats/{chat_id}/messages")
def send_message(chat_id: str, payload: MessageCreate):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    try:
        if not store.get_chat(chat_id):
            raise KeyError(chat_id)
        store.append_message(chat_id, "user", message)
        reply, usage = call_model(chat_id)
        store.append_message(chat_id, "assistant", reply)
        data = store.client_payload(chat_id, MAX_HISTORY_TOKENS)
        data["reply"] = reply
        data["usage"] = usage
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail="Chat not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/chats/{chat_id}/regenerate")
def regenerate(chat_id: str, payload: RegenerateRequest):
    try:
        chat = store.require_chat(chat_id)
        if payload.message and payload.message.strip():
            store.append_message(chat_id, "user", payload.message.strip())
        else:
            while chat.messages and chat.messages[-1].role == "assistant":
                chat.messages.pop()
        reply, usage = call_model(chat_id)
        store.append_message(chat_id, "assistant", reply)
        data = store.client_payload(chat_id, MAX_HISTORY_TOKENS)
        data["reply"] = reply
        data["usage"] = usage
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail="Chat not found.")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
