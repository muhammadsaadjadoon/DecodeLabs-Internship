from __future__ import annotations

import json
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Role = Literal["user", "assistant"]


def now_ts() -> float:
    return time.time()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:18]}"


def estimate_tokens(text: str) -> int:
    """Small dependency-free token estimate for UI stats and context trimming."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def clean_title(text: str, fallback: str = "New chat") -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return fallback
    text = re.sub(r"^[#>*\-\s]+", "", text)
    return text[:54].rstrip(".,:; ") or fallback


@dataclass
class Message:
    id: str
    role: Role
    content: str
    timestamp: float = field(default_factory=now_ts)

    @classmethod
    def create(cls, role: Role, content: str) -> "Message":
        return cls(id=new_id("msg"), role=role, content=content.strip(), timestamp=now_ts())

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Message":
        return cls(
            id=str(payload.get("id") or new_id("msg")),
            role="assistant" if payload.get("role") == "assistant" else "user",
            content=str(payload.get("content") or ""),
            timestamp=float(payload.get("timestamp") or now_ts()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class Chat:
    id: str
    title: str = "New chat"
    created_at: float = field(default_factory=now_ts)
    updated_at: float = field(default_factory=now_ts)
    messages: list[Message] = field(default_factory=list)
    pinned: bool = False

    @classmethod
    def create(cls, title: str | None = None) -> "Chat":
        return cls(id=new_id("chat"), title=clean_title(title or "New chat"), created_at=now_ts(), updated_at=now_ts())

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Chat":
        return cls(
            id=str(payload.get("id") or new_id("chat")),
            title=clean_title(str(payload.get("title") or "New chat")),
            created_at=float(payload.get("created_at") or now_ts()),
            updated_at=float(payload.get("updated_at") or now_ts()),
            messages=[Message.from_dict(m) for m in payload.get("messages", []) if isinstance(m, dict)],
            pinned=bool(payload.get("pinned", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "pinned": self.pinned,
            "messages": [m.to_dict() for m in self.messages],
        }

    def stats(self, max_history_tokens: int) -> dict[str, Any]:
        tokens = sum(estimate_tokens(m.content) for m in self.messages)
        return {
            "message_count": len(self.messages),
            "estimated_tokens": tokens,
            "max_history_tokens": max_history_tokens,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def preview(self) -> str:
        for message in reversed(self.messages):
            if message.content.strip():
                return clean_title(message.content, "No messages yet")[:92]
        return "No messages yet"


class ChatStore:
    """Thread-safe JSON storage. Designed for a local portfolio/demo app."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._chats: dict[str, Chat] = {}
        self._load()

    def _load(self) -> None:
        with self._lock:
            if not self.path.exists():
                self._chats = {}
                self._save_unlocked()
                return
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8") or "{}")
                chats = raw.get("chats", {}) if isinstance(raw, dict) else {}
                self._chats = {
                    chat_id: Chat.from_dict(chat_payload)
                    for chat_id, chat_payload in chats.items()
                    if isinstance(chat_payload, dict)
                }
            except Exception:
                backup = self.path.with_suffix(f".broken.{int(now_ts())}.json")
                try:
                    self.path.replace(backup)
                except Exception:
                    pass
                self._chats = {}
                self._save_unlocked()

    def _save_unlocked(self) -> None:
        payload = {
            "version": 1,
            "saved_at": now_ts(),
            "chats": {chat_id: chat.to_dict() for chat_id, chat in self._chats.items()},
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def list_chats(self) -> list[dict[str, Any]]:
        with self._lock:
            items = sorted(self._chats.values(), key=lambda c: (not c.pinned, -c.updated_at))
            return [
                {
                    "id": c.id,
                    "title": c.title,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at,
                    "message_count": len(c.messages),
                    "preview": c.preview(),
                    "pinned": c.pinned,
                }
                for c in items
            ]

    def create_chat(self, title: str | None = None) -> Chat:
        with self._lock:
            chat = Chat.create(title=title)
            self._chats[chat.id] = chat
            self._save_unlocked()
            return chat

    def get_chat(self, chat_id: str) -> Chat | None:
        with self._lock:
            return self._chats.get(chat_id)

    def require_chat(self, chat_id: str) -> Chat:
        chat = self.get_chat(chat_id)
        if not chat:
            raise KeyError(chat_id)
        return chat

    def update_chat(self, chat_id: str, *, title: str | None = None, pinned: bool | None = None) -> Chat:
        with self._lock:
            chat = self.require_chat(chat_id)
            if title is not None:
                chat.title = clean_title(title)
            if pinned is not None:
                chat.pinned = bool(pinned)
            chat.updated_at = now_ts()
            self._save_unlocked()
            return chat

    def delete_chat(self, chat_id: str) -> bool:
        with self._lock:
            existed = self._chats.pop(chat_id, None) is not None
            if existed:
                self._save_unlocked()
            return existed

    def clear_chat(self, chat_id: str) -> Chat:
        with self._lock:
            chat = self.require_chat(chat_id)
            chat.messages.clear()
            chat.updated_at = now_ts()
            self._save_unlocked()
            return chat

    def append_message(self, chat_id: str, role: Role, content: str) -> Message:
        content = (content or "").strip()
        if not content:
            raise ValueError("Message cannot be empty.")
        with self._lock:
            chat = self.require_chat(chat_id)
            message = Message.create(role=role, content=content)
            chat.messages.append(message)
            if role == "user" and (chat.title == "New chat" or not chat.title.strip()):
                chat.title = clean_title(content)
            chat.updated_at = now_ts()
            self._save_unlocked()
            return message

    def replace_last_assistant(self, chat_id: str, content: str) -> Message:
        content = (content or "").strip()
        if not content:
            raise ValueError("Message cannot be empty.")
        with self._lock:
            chat = self.require_chat(chat_id)
            for message in reversed(chat.messages):
                if message.role == "assistant":
                    message.content = content
                    message.timestamp = now_ts()
                    chat.updated_at = now_ts()
                    self._save_unlocked()
                    return message
            return self.append_message(chat_id, "assistant", content)

    def client_payload(self, chat_id: str, max_history_tokens: int) -> dict[str, Any]:
        with self._lock:
            chat = self.require_chat(chat_id)
            return {
                "id": chat.id,
                "title": chat.title,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
                "pinned": chat.pinned,
                "messages": [m.to_dict() for m in chat.messages],
                "stats": chat.stats(max_history_tokens),
            }

    def model_context(self, chat_id: str, max_messages: int, max_history_tokens: int) -> list[Message]:
        with self._lock:
            chat = self.require_chat(chat_id)
            selected: list[Message] = []
            tokens = 0
            for message in reversed(chat.messages[-max_messages:]):
                t = estimate_tokens(message.content)
                if selected and tokens + t > max_history_tokens:
                    break
                selected.append(message)
                tokens += t
            return list(reversed(selected))
