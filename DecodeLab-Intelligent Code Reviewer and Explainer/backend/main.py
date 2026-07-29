"""CodeFix AI FastAPI entrypoint.

Run with: uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.gemini_service import GeminiParsingError, explain_code, repair_code, review_code
from app.schemas import ExplainRequest, ExplainResponse, WorkspaceSettingsUpdate

try:
    from tree_sitter_language_pack import get_parser as get_tree_sitter_parser
except Exception:  # Optional fallback: language-specific tools still run.
    get_tree_sitter_parser = None

app = FastAPI(
    title="CodeFix AI",
    description="Professional code analysis, correction, and structured explanation.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent
STORAGE_DIR = ROOT / "storage"
DATABASE_PATH = STORAGE_DIR / "codefix.db"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CLIENT_COOKIE = "codefix_device_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 3
MAX_AVATAR_BYTES = 5 * 1024 * 1024

EXTENSION_LANGUAGE_MAP = {
    "py": "py", "js": "js", "jsx": "jsx", "ts": "ts", "tsx": "tsx",
    "java": "java", "cpp": "cpp", "cc": "cpp", "cxx": "cpp", "c": "c",
    "h": "h", "hpp": "hpp", "go": "go", "rb": "rb", "php": "php",
    "cs": "cs", "rs": "rs", "swift": "swift", "kt": "kt", "sql": "sql",
    "sh": "sh", "bash": "sh", "html": "html", "htm": "html", "css": "css",
}
LANGUAGE_ALIASES = {
    "python": "py", "py": "py",
    "javascript": "js", "js": "js", "node": "js", "nodejs": "js",
    "jsx": "jsx", "react": "jsx",
    "typescript": "ts", "ts": "ts", "tsx": "tsx",
    "java": "java", "cpp": "cpp", "c++": "cpp", "cc": "cpp", "cxx": "cpp",
    "c": "c", "h": "h", "hpp": "hpp", "header": "h",
    "go": "go", "golang": "go", "ruby": "rb", "rb": "rb",
    "php": "php", "csharp": "cs", "c#": "cs", "cs": "cs",
    "rust": "rs", "rs": "rs", "swift": "swift", "kotlin": "kt", "kt": "kt",
    "sql": "sql", "shell": "sh", "bash": "sh", "sh": "sh",
    "html": "html", "htm": "html", "css": "css", "text": "txt", "txt": "txt",
}
LANGUAGE_LABELS = {
    "py": "Python", "js": "JavaScript", "jsx": "JavaScript (JSX)",
    "ts": "TypeScript", "tsx": "TypeScript (TSX)", "java": "Java",
    "cpp": "C++", "c": "C", "h": "C/C++ Header", "hpp": "C++ Header",
    "go": "Go", "rb": "Ruby", "php": "PHP", "cs": "C#", "rs": "Rust",
    "swift": "Swift", "kt": "Kotlin", "sql": "SQL", "sh": "Shell",
    "html": "HTML", "css": "CSS", "txt": "Plain Text",
}
LANGUAGE_FAMILIES = {
    "js": "javascript", "jsx": "javascript", "ts": "javascript", "tsx": "javascript",
    "cpp": "cpp", "h": "cpp", "hpp": "cpp",
}
SUPPORTED_LANGUAGES = set(LANGUAGE_LABELS)
SUPPORTED_FOCUS = {"balanced", "correctness", "security", "performance"}
SUPPORTED_DETAIL = {"concise", "standard", "deep"}
SUPPORTED_THEME = {"dark", "light"}


@dataclass(frozen=True)
class LanguageDetection:
    language: str
    score: int
    confidence: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class LanguageResolution:
    language: str
    filename: str
    auto_detected: bool
    detection: Optional[LanguageDetection]


@dataclass(frozen=True)
class SyntaxValidation:
    status: str
    summary: str
    diagnostics: tuple[str, ...] = ()
    engines: tuple[str, ...] = ()


LANGUAGE_SIGNATURES: dict[str, tuple[tuple[str, int, str], ...]] = {
    "py": (
        (r"^\s*(?:async\s+)?def\s+[A-Za-z_]\w*\s*\([^\n]*\)\s*(?:->[^:]+)?\s*:", 16, "Python function definition"),
        (r"^\s*class\s+[A-Za-z_]\w*(?:\([^)]*\))?\s*:", 13, "Python class definition"),
        (r"^\s*(?:from\s+[\w.]+\s+import|import\s+[\w.]+)", 9, "Python import"),
        (r"if\s+__name__\s*==\s*[\"']__main__[\"']\s*:", 18, "Python entry point"),
        (r"^\s*(?:for\s+.+\s+in\s+.+|while\s+.+|if\s+.+|elif\s+.+|else|try|except(?:\s+.+)?|finally|with\s+.+)\s*:\s*$", 9, "Python block syntax"),
        (r"\b(?:print|input|len|range|enumerate|zip|isinstance)\s*\(", 11, "Python built-in call"),
        (r"\b(?:None|True|False|self|elif|yield|lambda|asyncio)\b", 5, "Python keyword"),
        (r"\[[^\]\n]+\s+for\s+[A-Za-z_]\w*\s+in\s+[^\]\n]+\]", 8, "Python comprehension"),
    ),
    "jsx": (
        (r"(?:from\s+[\"']react[\"']|require\([\"']react[\"']\))", 10, "React import"),
        (r"return\s*\(\s*<[A-Za-z][\w.-]*(?:\s|>)", 16, "JSX return tree"),
        (r"(?:=>|function\s+[A-Za-z_$]\w*)\s*\(?[^=\n]*\)?\s*=>?\s*<[A-Za-z]", 11, "JSX component expression"),
        (r"<[A-Z][A-Za-z0-9]*(?:\s|/?>)", 10, "JSX component"),
    ),
    "tsx": (
        (r"(?:interface|type)\s+[A-Z]\w*", 7, "TypeScript declaration"),
        (r"return\s*\(\s*<[A-Za-z][\w.-]*(?:\s|>)", 14, "TSX return tree"),
        (r"(?:React\.FC|JSX\.Element|Props\s*=|:\s*React\.)", 12, "TSX typing"),
    ),
    "ts": (
        (r"\binterface\s+[A-Za-z_]\w*", 14, "TypeScript interface"),
        (r"\btype\s+[A-Za-z_]\w*\s*=", 13, "TypeScript type alias"),
        (r"\benum\s+[A-Za-z_]\w*", 12, "TypeScript enum"),
        (r"(?:\(|,)\s*[A-Za-z_]\w*\??\s*:\s*(?:string|number|boolean|unknown|never|void|any|readonly|[A-Z]\w*(?:<[^>]+>)?)", 9, "TypeScript parameter annotation"),
        (r"\)\s*:\s*(?:string|number|boolean|void|Promise<|[A-Z]\w*)", 8, "TypeScript return annotation"),
        (r"\b(?:as\s+const|satisfies\s+[A-Z]\w*|implements\s+[A-Z]\w*)\b", 8, "TypeScript-only syntax"),
    ),
    "js": (
        (r"\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=", 8, "JavaScript declaration"),
        (r"=>", 7, "JavaScript arrow function"),
        (r"\bfunction\s+[A-Za-z_$][\w$]*\s*\(", 8, "JavaScript function"),
        (r"\b(?:console\.log|document\.|window\.|module\.exports|exports\.|require\s*\()", 12, "JavaScript runtime API"),
        (r"^\s*(?:import\s+.+\s+from|export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var))\b", 9, "JavaScript module syntax"),
        (r"\b(?:async\s+function|await\s+|new\s+Promise\s*\()", 6, "JavaScript asynchronous syntax"),
    ),
    "java": (
        (r"public\s+static\s+void\s+main\s*\(", 19, "Java entry point"),
        (r"System\.out\.print(?:ln)?\s*\(", 15, "Java console API"),
        (r"\bpublic\s+class\s+[A-Za-z_]\w*", 13, "Java public class"),
        (r"^\s*(?:package\s+[\w.]+\s*;|import\s+java\.)", 11, "Java package or import"),
        (r"\b(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?(?:void|int|long|double|boolean|String|List<)", 7, "Java member declaration"),
    ),
    "cpp": (
        (r"#include\s*<(?:iostream|vector|string|map|memory|algorithm)>", 18, "C++ standard header"),
        (r"\bstd::", 14, "C++ standard namespace"),
        (r"\b(?:cout|cin|cerr)\s*(?:<<|>>)", 13, "C++ stream operation"),
        (r"using\s+namespace\s+std\s*;", 13, "C++ namespace declaration"),
        (r"\btemplate\s*<", 10, "C++ template"),
        (r"\b(?:unique_ptr|shared_ptr|nullptr|constexpr|namespace)\b", 8, "C++ keyword"),
    ),
    "c": (
        (r"#include\s*<(?:stdio\.h|stdlib\.h|string\.h)>", 16, "C standard header"),
        (r"\b(?:printf|scanf|malloc|calloc|realloc|free|sizeof)\s*\(", 12, "C library API"),
        (r"\bstruct\s+[A-Za-z_]\w*\s*\{", 8, "C struct"),
        (r"\bint\s+main\s*\([^)]*\)\s*\{", 7, "C entry point"),
    ),
    "cs": (
        (r"^\s*using\s+System(?:\.|;)", 18, "C# System import"),
        (r"Console\.Write(?:Line)?\s*\(", 15, "C# console API"),
        (r"\bnamespace\s+[A-Za-z_]\w*", 10, "C# namespace"),
        (r"\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:class|record|interface|void|string|int|bool)\b", 8, "C# declaration"),
        (r"\b(?:async\s+Task|IEnumerable<|List<|DateTime|var\s+\w+\s*=\s*new\s+)", 6, "C# framework syntax"),
    ),
    "go": (
        (r"^\s*package\s+(?:main|[A-Za-z_]\w*)", 18, "Go package declaration"),
        (r"\bfunc\s+(?:\([^)]*\)\s*)?[A-Za-z_]\w*\s*\(", 14, "Go function"),
        (r"\bfmt\.(?:Print|Printf|Println|Sprintf)\s*\(", 13, "Go fmt API"),
        (r":=", 7, "Go short declaration"),
        (r"\bgo\s+[A-Za-z_]\w*\s*\(|\bchan\s+\w+", 7, "Go concurrency syntax"),
    ),
    "rs": (
        (r"\bfn\s+main\s*\(\s*\)", 16, "Rust entry point"),
        (r"\b(?:println|print|eprintln)!\s*\(", 14, "Rust macro"),
        (r"\blet\s+mut\s+", 10, "Rust mutable binding"),
        (r"^\s*(?:use\s+std::|impl\s+|pub\s+(?:struct|enum|trait)\s+)", 10, "Rust declaration"),
        (r"\b(?:Option<|Result<|Some\(|None\b|match\s+\w+\s*\{)", 7, "Rust type or match syntax"),
    ),
    "swift": (
        (r"^\s*import\s+(?:Foundation|SwiftUI|UIKit)", 17, "Swift framework import"),
        (r"\bfunc\s+[A-Za-z_]\w*\s*\([^)]*\)\s*(?:->\s*[^\{]+)?\s*\{", 12, "Swift function"),
        (r"\b(?:guard\s+let|if\s+let)\b", 11, "Swift optional binding"),
        (r"\b(?:let|var)\s+[A-Za-z_]\w*\s*:\s*(?:String|Int|Double|Bool|[A-Z]\w*)", 8, "Swift typed binding"),
        (r"\bprint\s*\(", 4, "Swift print call"),
    ),
    "kt": (
        (r"\bfun\s+main\s*\(", 17, "Kotlin entry point"),
        (r"\bdata\s+class\s+[A-Za-z_]\w*", 14, "Kotlin data class"),
        (r"\b(?:val|var)\s+[A-Za-z_]\w*\s*(?::[^=\n]+)?=", 9, "Kotlin property"),
        (r"\bprintln\s*\(", 10, "Kotlin output"),
        (r"\b(?:when\s*\(|object\s*:\s*|companion\s+object|suspend\s+fun)\b", 9, "Kotlin-specific syntax"),
    ),
    "php": (
        (r"<\?php", 24, "PHP opening tag"),
        (r"\$[A-Za-z_]\w*\s*(?:=|->|\[)", 11, "PHP variable"),
        (r"\b(?:echo|namespace|use|require_once|include_once)\s+", 9, "PHP keyword"),
    ),
    "rb": (
        (r"^\s*def\s+[A-Za-z_]\w*[!?=]?(?:\([^\n]*\))?\s*$", 13, "Ruby method"),
        (r"^\s*(?:class|module)\s+[A-Z]\w*", 12, "Ruby class or module"),
        (r"\b(?:puts|require|attr_accessor|attr_reader)\b", 11, "Ruby API"),
        (r"\bdo\s*\|[^|]+\|", 9, "Ruby block"),
        (r"^\s*end\s*$", 5, "Ruby end keyword"),
    ),
    "sql": (
        (r"\bSELECT\b[\s\S]+\bFROM\b", 19, "SQL SELECT statement"),
        (r"\b(?:CREATE\s+TABLE|ALTER\s+TABLE|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE)\b", 18, "SQL data statement"),
        (r"\b(?:JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|WHERE|LIMIT)\b", 7, "SQL clause"),
    ),
    "sh": (
        (r"^#!\s*/(?:usr/bin/env\s+|(?:usr/)?bin/)?(?:ba|z|k)?sh", 22, "shell shebang"),
        (r"\b(?:then|fi|done|esac)\b", 12, "shell control keyword"),
        (r"\$\([^)]+\)|\$\{[^}]+\}", 9, "shell expansion"),
        (r"^\s*(?:echo|export|source|chmod|mkdir|grep|sed|awk)\b", 7, "shell command"),
    ),
    "html": (
        (r"<!doctype\s+html", 24, "HTML document declaration"),
        (r"<html(?:\s|>)", 20, "HTML root element"),
        (r"<(?:head|body|main|section|article|nav|header|footer|div|form|input|button)(?:\s|>)", 13, "HTML element"),
        (r"</[a-z][\w-]*\s*>", 7, "HTML closing tag"),
    ),
    "css": (
        (r"(?:^|\})\s*(?:[.#][\w-]+|:root|\*|(?:html|body|main|section|article|button|input|textarea|nav|header|footer)(?:[\s.#:[>+~][^{]*)?)\s*\{[\s\S]*?[\w-]+\s*:\s*[^;{}]+;?", 20, "CSS selector and declaration block"),
        (r"@(?:media|supports|keyframes|font-face|import|layer|tailwind)\b", 15, "CSS at-rule"),
        (r"--[\w-]+\s*:\s*[^;{}]+;", 11, "CSS custom property"),
        (r"\b(?:display|color|background|margin|padding|font-size|grid-template|border-radius|position|width|height)\s*:\s*[^;{}]+", 7, "CSS property"),
    ),
}

HARD_LANGUAGE_MATCHES: tuple[tuple[str, str, str], ...] = (
    ("php", r"<\?php", "PHP opening tag"),
    ("tsx", r"(?:React\.FC|JSX\.Element)[\s\S]*<[A-Za-z]|(?:interface|type)\s+[A-Z]\w*[\s\S]*return\s*\(\s*<", "TSX structure"),
    ("jsx", r"(?:from\s+[\"']react[\"']|return\s*\(\s*<[A-Za-z]|=>\s*<[A-Za-z])", "JSX structure"),
    ("html", r"<!doctype\s+html|<html(?:\s|>)", "HTML document"),
    ("sh", r"^#!\s*/(?:usr/bin/env\s+|(?:usr/)?bin/)?(?:ba|z|k)?sh", "shell shebang"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                client_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL DEFAULT '',
                professional_role TEXT NOT NULL DEFAULT '',
                avatar_path TEXT,
                avatar_data BLOB,
                avatar_mime TEXT,
                focus TEXT NOT NULL DEFAULT 'balanced',
                detail TEXT NOT NULL DEFAULT 'standard',
                auto_explain INTEGER NOT NULL DEFAULT 0,
                theme TEXT NOT NULL DEFAULT 'dark',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                language TEXT NOT NULL,
                source_code TEXT NOT NULL,
                bug_report TEXT NOT NULL,
                refactored_code TEXT NOT NULL,
                has_issues INTEGER NOT NULL,
                model_used TEXT NOT NULL,
                explanation TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(client_id) REFERENCES workspaces(client_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_reviews_client_updated
                ON reviews(client_id, updated_at DESC);
            """
        )
        workspace_columns = {row["name"] for row in conn.execute("PRAGMA table_info(workspaces)").fetchall()}
        if "avatar_data" not in workspace_columns:
            conn.execute("ALTER TABLE workspaces ADD COLUMN avatar_data BLOB")
        if "avatar_mime" not in workspace_columns:
            conn.execute("ALTER TABLE workspaces ADD COLUMN avatar_mime TEXT")

        # Keep existing saved chats consistent with the new filename-based naming rule.
        conn.execute(
            """
            UPDATE reviews
            SET title = filename
            WHERE TRIM(COALESCE(filename, '')) <> ''
              AND title <> filename
            """
        )


init_db()


def migrate_legacy_avatars() -> None:
    """Move legacy avatar files into the backend database and remove local copies."""
    with db() as conn:
        rows = conn.execute(
            "SELECT client_id, avatar_path, avatar_data FROM workspaces WHERE avatar_path IS NOT NULL"
        ).fetchall()
        for row in rows:
            if row["avatar_data"]:
                continue
            path = Path(row["avatar_path"] or "")
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(suffix)
            if not mime:
                continue
            try:
                data = path.read_bytes()
                conn.execute(
                    "UPDATE workspaces SET avatar_data=?, avatar_mime=?, avatar_path=NULL WHERE client_id=?",
                    (data, mime, row["client_id"]),
                )
                path.unlink(missing_ok=True)
            except OSError:
                continue


migrate_legacy_avatars()


def valid_client_id(value: Optional[str]) -> bool:
    return bool(value and re.fullmatch(r"[0-9a-fA-F-]{36}", value))


def ensure_client(request: Request, response: Response) -> str:
    current = request.cookies.get(CLIENT_COOKIE)
    client_id = current if valid_client_id(current) else str(uuid.uuid4())
    response.set_cookie(
        key=CLIENT_COOKIE,
        value=client_id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    now = utc_now()
    with db() as conn:
        conn.execute(
            """
            INSERT INTO workspaces(client_id, display_name, professional_role, created_at, updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(client_id) DO NOTHING
            """,
            (client_id, "", "", now, now),
        )
    return client_id


def normalize_language(value: Optional[str]) -> Optional[str]:
    normalized = (value or "").strip().lower().lstrip(".")
    return LANGUAGE_ALIASES.get(normalized)


def language_family(language: str) -> str:
    return LANGUAGE_FAMILIES.get(language, language)


def same_language_family(first: str, second: str) -> bool:
    return language_family(first) == language_family(second)


def language_from_filename(filename: str) -> Optional[str]:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return EXTENSION_LANGUAGE_MAP.get(extension)


def replace_filename_extension(filename: str, language: str) -> str:
    clean = clean_filename(filename or "snippet")
    preferred_extension = LANGUAGE_LABELS.get(language) and language or "txt"
    # Header aliases should retain their conventional extension.
    if language in {"h", "hpp"}:
        preferred_extension = language
    stem = clean.rsplit(".", 1)[0] if "." in clean else clean
    return f"{stem or 'snippet'}.{preferred_extension}"


def detect_language_from_code(source_code: str) -> Optional[LanguageDetection]:
    code = (source_code or "").strip()
    if len(code) < 4:
        return None

    for language, pattern, reason in HARD_LANGUAGE_MATCHES:
        flags = re.MULTILINE | re.DOTALL | (re.IGNORECASE if language in {"html", "php"} else 0)
        if re.search(pattern, code, flags):
            return LanguageDetection(language, 30, 0.99, (reason,))

    if (
        re.search(r"^\s*(?:print|input|len|range)\s*\([^\n]*\)\s*$", code, re.MULTILINE)
        and not re.search(r"[;{}]", code)
        and not re.search(r"\b(?:let|var|val|func|fun)\b", code)
    ):
        return LanguageDetection("py", 24, 0.99, ("Python built-in expression",))

    candidates: list[tuple[str, int, tuple[str, ...]]] = []
    for language, rules in LANGUAGE_SIGNATURES.items():
        score = 0
        evidence: list[str] = []
        flags = re.MULTILINE | re.DOTALL
        if language in {"html", "css", "php", "sql"}:
            flags |= re.IGNORECASE
        for pattern, weight, reason in rules:
            if re.search(pattern, code, flags):
                score += weight
                evidence.append(reason)

        if language == "css" and re.search(r"\b(?:def|print|import|from|console\.log|function|const|let|var)\b", code):
            score -= 14
        if language == "py" and re.search(r"(?:=>|console\.log|System\.out|std::|#include\s*<|\bpackage\s+main\b)", code):
            score -= 14
        if language == "js" and re.search(r"\b(?:interface|type)\s+[A-Z]\w*|:\s*(?:string|number|boolean)\b", code):
            score -= 7
        if language == "html" and re.search(r"(?:return\s*\(|=>)\s*<[A-Za-z]|from\s+[\"']react[\"']", code):
            score -= 12
        if language == "php" and not re.search(r"<\?php", code, re.IGNORECASE) and not re.search(r"\$[A-Za-z_]\w*", code):
            score -= 12
        if language == "sh" and re.search(r"(?:^|\n)\s*(?:import|export)\s+|=>|\bfunction\s+|console\.", code, re.MULTILINE):
            score -= 18
        if language == "sql" and re.search(r"(?:^|\n)\s*(?:import|export)\s+|\b(?:const|let|var|function)\s+|=>", code, re.MULTILINE):
            score -= 24

        candidates.append((language, score, tuple(evidence)))

    candidates.sort(key=lambda item: item[1], reverse=True)
    best_language, best_score, evidence = candidates[0]
    runner_up_score = candidates[1][1] if len(candidates) > 1 else 0
    if best_score < 7:
        return None

    margin = best_score - max(0, runner_up_score)
    if margin < 2 and best_score < 15:
        return None

    confidence = min(0.99, 0.58 + (best_score / 60) + (max(0, margin) / 50))
    return LanguageDetection(best_language, best_score, confidence, evidence)


def resolve_submission_language(
    source_code: str,
    filename: str,
    explicit_language: Optional[str],
    *,
    uploaded_file: bool,
) -> LanguageResolution:
    selected = normalize_language(explicit_language)
    extension_language = language_from_filename(filename)
    detection = detect_language_from_code(source_code)
    strong_detection = bool(detection and detection.score >= 7 and detection.confidence >= 0.58)

    if explicit_language and selected is None:
        raise HTTPException(
            status_code=422,
            detail="The selected programming language is not supported. Choose a language from the available list.",
        )

    if uploaded_file:
        if extension_language is None and not strong_detection:
            raise HTTPException(
                status_code=422,
                detail="CodeFix AI could not identify this file type. Rename the file with a supported source-code extension and try again.",
            )
        resolved = extension_language or (detection.language if detection else None)
        if resolved is None:
            raise HTTPException(status_code=422, detail="The source language could not be identified reliably.")
        if strong_detection and not same_language_family(resolved, detection.language):
            expected = LANGUAGE_LABELS.get(resolved, resolved)
            detected_label = LANGUAGE_LABELS.get(detection.language, detection.language)
            raise HTTPException(
                status_code=422,
                detail=(
                    f"The uploaded file is named as {expected}, but its contents are identified as {detected_label}. "
                    "Rename the file with the matching extension before starting the review."
                ),
            )
        return LanguageResolution(resolved, clean_filename(filename), False, detection)

    if strong_detection:
        resolved = detection.language
        auto_detected = selected != resolved or extension_language != resolved
    else:
        resolved = selected or extension_language or "txt"
        auto_detected = False

    if resolved not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail="The source language could not be identified reliably.")

    aligned_filename = replace_filename_extension(filename, resolved)
    return LanguageResolution(resolved, aligned_filename, auto_detected, detection)


TREE_SITTER_LANGUAGE_MAP = {
    "py": "python",
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "tsx",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "h": "cpp",
    "hpp": "cpp",
    "go": "go",
    "rb": "ruby",
    "php": "php",
    "cs": ("c_sharp", "csharp"),
    "rs": "rust",
    "swift": "swift",
    "kt": "kotlin",
    "sql": "sql",
    "sh": "bash",
    "html": "html",
    "css": "css",
}


def _dedupe_diagnostics(items: list[str], limit: int = 12) -> tuple[str, ...]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = re.sub(r"\s+", " ", str(item or "")).strip(" -\n\t")
        if not cleaned or cleaned.lower() in seen:
            continue
        seen.add(cleaned.lower())
        output.append(cleaned)
        if len(output) >= limit:
            break
    return tuple(output)


def _validation_result(
    *, language: str, diagnostics: list[str], engines: list[str]
) -> SyntaxValidation:
    clean_diagnostics = _dedupe_diagnostics(diagnostics)
    clean_engines = tuple(dict.fromkeys(engine for engine in engines if engine))
    label = LANGUAGE_LABELS.get(language, language)
    if clean_diagnostics:
        details = "; ".join(clean_diagnostics)
        return SyntaxValidation(
            "failed",
            f"Deterministic {label} validation found {len(clean_diagnostics)} confirmed issue(s): {details}",
            clean_diagnostics,
            clean_engines,
        )
    if clean_engines:
        engine_label = ", ".join(clean_engines)
        return SyntaxValidation(
            "passed",
            f"Deterministic {label} validation completed successfully using {engine_label}.",
            (),
            clean_engines,
        )
    return SyntaxValidation(
        "not_available",
        f"No deterministic parser or compiler was available for {label}; the review will use two-stage verified static analysis.",
        (),
        (),
    )


def _tree_sitter_diagnostics(source_code: str, language: str) -> tuple[list[str], bool]:
    grammar_names = TREE_SITTER_LANGUAGE_MAP.get(language)
    if not grammar_names or get_tree_sitter_parser is None:
        return [], False
    if isinstance(grammar_names, str):
        grammar_names = (grammar_names,)
    parser = None
    for grammar in grammar_names:
        try:
            parser = get_tree_sitter_parser(grammar)
            break
        except Exception:
            continue
    if parser is None:
        return [], False
    try:
        source_bytes = source_code.encode("utf-8")
        tree = parser.parse(source_bytes)
    except Exception:
        return [], False

    diagnostics: list[str] = []
    stack = [tree.root_node]
    while stack and len(diagnostics) < 12:
        node = stack.pop()
        node_type = str(getattr(node, "type", ""))
        is_missing = bool(getattr(node, "is_missing", False))
        is_error = node_type == "ERROR" or is_missing
        if is_error:
            point = getattr(node, "start_point", (0, 0))
            line = int(point[0]) + 1
            column = int(point[1]) + 1
            start_byte = int(getattr(node, "start_byte", 0))
            end_byte = int(getattr(node, "end_byte", start_byte))
            excerpt = source_bytes[start_byte:end_byte].decode("utf-8", errors="replace")
            excerpt = re.sub(r"\s+", " ", excerpt).strip()[:90]
            if is_missing:
                diagnostics.append(
                    f"line {line}, column {column}: missing {node_type or 'required syntax token'}."
                )
            else:
                shown = f" near `{excerpt}`" if excerpt else ""
                diagnostics.append(f"line {line}, column {column}: invalid {label_for_node(node_type)}{shown}.")
        if bool(getattr(node, "has_error", False)) or is_error:
            stack.extend(reversed(list(getattr(node, "children", ()))))
    return diagnostics, True


def label_for_node(node_type: str) -> str:
    return "syntax" if not node_type or node_type == "ERROR" else node_type.replace("_", " ")


def _clean_process_output(raw: str, temporary_path: str, filename: str) -> list[str]:
    text = (raw or "").replace(temporary_path, filename)
    text = text.replace(str(Path(temporary_path).parent), "")
    output: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if re.fullmatch(r"[\^~\-\s]+", cleaned):
            continue
        if cleaned.startswith(("at ", "Node.js v", "npm notice")):
            continue
        output.append(cleaned[:300])
    return output[:12]


def _run_source_tool(
    source_code: str,
    *,
    suffix: str,
    command_builder,
    filename: str,
    timeout: int = 10,
) -> tuple[list[str], bool]:
    temporary_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=suffix, encoding="utf-8", delete=False) as handle:
            handle.write(source_code)
            temporary_path = handle.name
        command = command_builder(temporary_path)
        if not command:
            return [], False
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if completed.returncode == 0:
            return [], True
        raw = "\n".join(part for part in (completed.stderr, completed.stdout) if part)
        return _clean_process_output(raw, temporary_path, filename), True
    except (OSError, subprocess.SubprocessError):
        return [], False
    finally:
        if temporary_path:
            try:
                Path(temporary_path).unlink(missing_ok=True)
            except OSError:
                pass


def _delimiter_diagnostics(source_code: str, language: str) -> list[str]:
    """Find unmatched (), [] and {} while ignoring strings and common comments."""
    if language in {"py", "html", "css", "txt"}:
        return []
    pairs = {")": "(", "]": "[", "}": "{"}
    opening = set(pairs.values())
    stack: list[tuple[str, int, int]] = []
    diagnostics: list[str] = []
    line = 1
    column = 0
    index = 0
    string_quote: Optional[str] = None
    triple_quote = False
    escaped = False
    line_comment = False
    block_comment = False

    while index < len(source_code):
        char = source_code[index]
        nxt = source_code[index + 1] if index + 1 < len(source_code) else ""
        column += 1
        if char == "\n":
            line += 1
            column = 0
            line_comment = False
            index += 1
            continue
        if line_comment:
            index += 1
            continue
        if block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 2
                column += 1
            else:
                index += 1
            continue
        if string_quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif triple_quote and source_code[index:index + 3] == string_quote * 3:
                string_quote = None
                triple_quote = False
                index += 3
                column += 2
                continue
            elif not triple_quote and char == string_quote:
                string_quote = None
            index += 1
            continue

        if char == "/" and nxt == "*":
            block_comment = True
            index += 2
            column += 1
            continue
        if char == "/" and nxt == "/":
            line_comment = True
            index += 2
            column += 1
            continue
        if char == "#" and language in {"rb", "sh"}:
            line_comment = True
            index += 1
            continue
        if char in {"'", '"', "`"}:
            if source_code[index:index + 3] == char * 3:
                string_quote = char
                triple_quote = True
                index += 3
                column += 2
                continue
            string_quote = char
            index += 1
            continue
        if char in opening:
            stack.append((char, line, column))
        elif char in pairs:
            if not stack or stack[-1][0] != pairs[char]:
                diagnostics.append(
                    f"line {line}, column {column}: unexpected closing delimiter `{char}`."
                )
            else:
                stack.pop()
        index += 1

    for char, open_line, open_column in stack[-6:]:
        expected = {"(": ")", "[": "]", "{": "}"}[char]
        diagnostics.append(
            f"line {open_line}, column {open_column}: opening delimiter `{char}` is missing closing `{expected}`."
        )
    if string_quote:
        diagnostics.append(f"line {line}: string literal is not terminated.")
    if block_comment:
        diagnostics.append("Block comment is not terminated.")
    return diagnostics


def _sql_diagnostics(source_code: str) -> list[str]:
    diagnostics: list[str] = []
    for match in re.finditer(r"\bSELECT\s+FROM\b", source_code, re.IGNORECASE):
        line = source_code.count("\n", 0, match.start()) + 1
        diagnostics.append(f"line {line}: `SELECT` is missing its projection list before `FROM`.")
    for match in re.finditer(r"\b(?:WHERE|AND|OR)\s*(?:;|$)", source_code, re.IGNORECASE | re.MULTILINE):
        line = source_code.count("\n", 0, match.start()) + 1
        keyword = match.group(0).strip(" ;\n\r\t")
        diagnostics.append(f"line {line}: `{keyword}` is missing a required condition expression.")
    return diagnostics


def _css_diagnostics(source_code: str) -> list[str]:
    """Validate CSS declarations without misreading multiline property values as new declarations."""
    # Preserve newlines so diagnostics continue to match the submitted source.
    clean = re.sub(
        r"/\*.*?\*/",
        lambda match: "\n" * match.group(0).count("\n"),
        source_code,
        flags=re.DOTALL,
    )
    diagnostics: list[str] = []
    class_names = set(re.findall(r"\.([A-Za-z_][\w-]*)", clean))

    # Retain the useful missing-class-prefix heuristic, but keep it independent from
    # declaration parsing so multiline values cannot create false positives.
    for line_number, raw_line in enumerate(clean.splitlines(), start=1):
        line = raw_line.strip()
        selector_match = re.match(r"^([a-z][\w-]+)(?=[\s.#:\[>+~][^{]*\{)", line)
        if selector_match and selector_match.group(1) in class_names:
            name = selector_match.group(1)
            diagnostics.append(
                f"line {line_number}: selector `{name}` matches the existing class `.{name}` but omits the class prefix (`.`)."
            )

    depth = 0
    parenthesis_depth = 0
    quote: str | None = None
    escaped = False
    statement: list[str] = []
    statement_line = 1
    line_number = 1

    def validate_statement(raw_statement: str, start_line: int) -> None:
        candidate = raw_statement.strip()
        if not candidate or candidate.startswith("@"):
            return
        # A complete declaration may span many lines, for example:
        # background:\n  radial-gradient(...),\n  var(--bg);
        if ":" not in candidate:
            if re.match(r"^[A-Za-z_-][\w-]*(?:\s+.+|.*[%#)])$", candidate, re.DOTALL):
                compact = re.sub(r"\s+", " ", candidate)
                diagnostics.append(
                    f"line {start_line}: malformed CSS declaration `{compact}`; expected `property: value`."
                )
            return
        property_name, value = candidate.split(":", 1)
        property_name = property_name.strip()
        if property_name and not re.fullmatch(r"(?:--)?-?[A-Za-z_][\w-]*", property_name):
            diagnostics.append(f"line {start_line}: invalid CSS property token `{property_name}`.")
            return
        if not value.strip():
            diagnostics.append(f"line {start_line}: CSS property `{property_name}` has no value.")
            return

        # Detect a second declaration that begins on a new line without a separating
        # semicolon, while allowing normal multiline function/value continuation lines.
        value_lines = value.splitlines()
        for offset, continuation in enumerate(value_lines[1:], start=1):
            stripped = continuation.strip()
            if re.match(r"^(?:--)?-?[A-Za-z_][\w-]*\s*:", stripped):
                diagnostics.append(
                    f"line {start_line + offset}: CSS declaration `{stripped}` must be preceded by a semicolon."
                )
                break

    for char in clean:
        if char == "\n":
            line_number += 1
        if escaped:
            escaped = False
            if depth > 0:
                statement.append(char)
            continue
        if char == "\\" and quote:
            escaped = True
            if depth > 0:
                statement.append(char)
            continue
        if quote:
            if char == quote:
                quote = None
            if depth > 0:
                statement.append(char)
            continue
        if char in {'"', "'"}:
            quote = char
            if depth > 0:
                statement.append(char)
            continue
        if char == "(":
            parenthesis_depth += 1
            if depth > 0:
                statement.append(char)
            continue
        if char == ")":
            parenthesis_depth = max(0, parenthesis_depth - 1)
            if depth > 0:
                statement.append(char)
            continue
        if char == "{" and parenthesis_depth == 0:
            depth += 1
            statement = []
            statement_line = line_number
            continue
        if char == "}" and parenthesis_depth == 0:
            if depth <= 0:
                diagnostics.append(f"line {line_number}: unexpected closing block brace `}}`.")
                depth = 0
            else:
                validate_statement("".join(statement), statement_line)
                depth -= 1
            statement = []
            statement_line = line_number
            continue
        if depth > 0 and char == ";" and parenthesis_depth == 0:
            validate_statement("".join(statement), statement_line)
            statement = []
            statement_line = line_number
            continue
        if depth > 0:
            if not statement and not char.isspace():
                statement_line = line_number
            statement.append(char)

    if quote:
        diagnostics.append(f"line {line_number}: CSS contains an unterminated quoted string.")
    if parenthesis_depth != 0:
        diagnostics.append("CSS function parentheses are incomplete or unbalanced.")
    if depth != 0:
        diagnostics.append("CSS block structure is incomplete because opening and closing braces do not match.")
    return diagnostics


def _html_diagnostics(source_code: str) -> list[str]:
    """Conservative HTML structure validation with real tag nesting evidence."""
    diagnostics: list[str] = []
    if source_code.count("<!--") != source_code.count("-->"):
        diagnostics.append("HTML contains an unterminated comment block.")
    if re.search(r"<[^>]*$", source_code.strip()):
        line = source_code.count("\n") + 1
        diagnostics.append(f"line {line}: HTML tag is missing its closing `>` delimiter.")

    clean = re.sub(r"<!--.*?-->", "", source_code, flags=re.DOTALL)
    clean = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1\s*>",
        lambda match: "\n" * match.group(0).count("\n"),
        clean,
        flags=re.IGNORECASE | re.DOTALL,
    )
    void_tags = {
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr",
    }
    optional_end_tags = {
        "html", "head", "body", "p", "li", "dt", "dd", "rt", "rp",
        "optgroup", "option", "colgroup", "thead", "tbody", "tfoot", "tr", "td", "th",
    }
    stack: list[tuple[str, int]] = []
    tag_pattern = re.compile(r"<\s*(/?)\s*([A-Za-z][\w:-]*)(?:\s[^<>]*?)?\s*(/?)>", re.DOTALL)
    for match in tag_pattern.finditer(clean):
        closing, raw_tag, self_closing = match.groups()
        tag = raw_tag.lower()
        line = clean.count("\n", 0, match.start()) + 1
        if tag in void_tags or self_closing:
            continue
        if not closing:
            # HTML permits a defined set of omitted end tags. Opening another item
            # of the same optional type implicitly closes the previous one.
            if tag in optional_end_tags and stack and stack[-1][0] == tag:
                stack.pop()
            stack.append((tag, line))
            continue
        if not stack:
            diagnostics.append(f"line {line}: closing tag `</{tag}>` has no matching opening tag.")
            continue
        if stack[-1][0] == tag:
            stack.pop()
            continue
        # Locate the matching ancestor. A mismatch is definite malformed nesting.
        ancestor_index = next((index for index in range(len(stack) - 1, -1, -1) if stack[index][0] == tag), -1)
        if ancestor_index < 0:
            diagnostics.append(f"line {line}: closing tag `</{tag}>` has no matching opening tag.")
        else:
            intervening = stack[ancestor_index + 1:]
            required_intervening = [(name, opened) for name, opened in intervening if name not in optional_end_tags]
            if required_intervening:
                open_tag, open_line = required_intervening[-1]
                diagnostics.append(
                    f"line {line}: `</{tag}>` closes before `<{open_tag}>` opened on line {open_line}; HTML tags are improperly nested."
                )
            del stack[ancestor_index:]

    for tag, line in stack[-8:]:
        if tag not in optional_end_tags:
            diagnostics.append(f"line {line}: opening tag `<{tag}>` is missing its closing `</{tag}>` tag.")
    return diagnostics


def _external_tool_diagnostics(
    source_code: str, language: str, filename: str
) -> tuple[list[str], list[str]]:
    diagnostics: list[str] = []
    engines: list[str] = []

    if language == "py":
        try:
            ast.parse(source_code, filename=filename)
        except SyntaxError as exc:
            line = exc.lineno or 1
            column = exc.offset or 1
            diagnostics.append(f"line {line}, column {column}: Python syntax error: {exc.msg}.")
        engines.append("Python AST")
        return diagnostics, engines

    if language == "js" and shutil.which("node"):
        found, available = _run_source_tool(
            source_code,
            suffix=".mjs" if re.search(r"^\s*(?:import|export)\b", source_code, re.MULTILINE) else ".js",
            command_builder=lambda path: [shutil.which("node"), "--check", path],
            filename=filename,
        )
        if available:
            engines.append("Node syntax checker")
            diagnostics.extend(found)

    if language == "jsx" and shutil.which("tsc"):
        found, available = _run_source_tool(
            source_code,
            suffix=".jsx",
            command_builder=lambda path: [
                shutil.which("tsc"), "--allowJs", "--noEmit", "--pretty", "false",
                "--skipLibCheck", "--target", "ES2022", "--module", "ESNext",
                "--jsx", "preserve", path,
            ],
            filename=filename,
            timeout=15,
        )
        if available:
            engines.append("JSX/TypeScript parser")
            diagnostics.extend(line for line in found if re.search(r"error TS1\d{3}", line))

    if language in {"ts", "tsx"} and shutil.which("tsc"):
        found, available = _run_source_tool(
            source_code,
            suffix=f".{language}",
            command_builder=lambda path: [
                shutil.which("tsc"),
                "--noEmit",
                "--pretty", "false",
                "--skipLibCheck",
                "--target", "ES2022",
                "--module", "ESNext",
                "--jsx", "preserve",
                path,
            ],
            filename=filename,
            timeout=15,
        )
        if available:
            engines.append("TypeScript parser")
            diagnostics.extend(line for line in found if re.search(r"error TS1\d{3}", line))

    if language in {"c", "cpp", "h", "hpp"}:
        compiler = shutil.which("clang++" if language in {"cpp", "hpp"} else "clang") or shutil.which(
            "g++" if language in {"cpp", "hpp"} else "gcc"
        )
        if compiler:
            dialect = "c++" if language in {"cpp", "hpp"} else "c"
            suffix = ".cpp" if dialect == "c++" else ".c"
            found, available = _run_source_tool(
                source_code,
                suffix=suffix,
                command_builder=lambda path: [compiler, "-fsyntax-only", "-x", dialect, path],
                filename=filename,
            )
            if available:
                engines.append(f"{Path(compiler).name} syntax checker")
                diagnostics.extend(line for line in found if "error:" in line.lower() and "file not found" not in line.lower())

    if language == "go" and shutil.which("gofmt"):
        found, available = _run_source_tool(
            source_code,
            suffix=".go",
            command_builder=lambda path: [shutil.which("gofmt"), "-e", path],
            filename=filename,
        )
        if available:
            engines.append("gofmt parser")
            diagnostics.extend(found)

    if language == "rb" and shutil.which("ruby"):
        found, available = _run_source_tool(
            source_code,
            suffix=".rb",
            command_builder=lambda path: [shutil.which("ruby"), "-c", path],
            filename=filename,
        )
        if available:
            engines.append("Ruby parser")
            diagnostics.extend(line for line in found if "syntax error" in line.lower() or "unexpected" in line.lower())

    if language == "php" and shutil.which("php"):
        found, available = _run_source_tool(
            source_code,
            suffix=".php",
            command_builder=lambda path: [shutil.which("php"), "-l", path],
            filename=filename,
        )
        if available:
            engines.append("PHP parser")
            diagnostics.extend(line for line in found if "error" in line.lower())

    if language == "sh" and shutil.which("bash"):
        found, available = _run_source_tool(
            source_code,
            suffix=".sh",
            command_builder=lambda path: [shutil.which("bash"), "-n", path],
            filename=filename,
        )
        if available:
            engines.append("Bash parser")
            diagnostics.extend(found)

    if language == "swift" and shutil.which("swiftc"):
        found, available = _run_source_tool(
            source_code,
            suffix=".swift",
            command_builder=lambda path: [shutil.which("swiftc"), "-parse", path],
            filename=filename,
            timeout=15,
        )
        if available:
            engines.append("Swift parser")
            diagnostics.extend(line for line in found if "error:" in line.lower())

    if language == "java" and shutil.which("javac"):
        found, available = _run_source_tool(
            source_code,
            suffix=".java",
            command_builder=lambda path: [shutil.which("javac"), "-proc:none", "-Xlint:none", path],
            filename=filename,
            timeout=15,
        )
        if available:
            engines.append("Java parser")
            syntax_patterns = re.compile(
                r"(;|\)|\}|\{|identifier|expression|statement).*(expected)|illegal start|reached end|unclosed|not a statement|class, interface|orphaned|else without",
                re.IGNORECASE,
            )
            diagnostics.extend(line for line in found if "error:" in line.lower() and syntax_patterns.search(line))

    if language == "kt" and shutil.which("kotlinc"):
        found, available = _run_source_tool(
            source_code,
            suffix=".kt",
            command_builder=lambda path: [shutil.which("kotlinc"), path, "-d", f"{path}.jar"],
            filename=filename,
            timeout=20,
        )
        try:
            pass
        finally:
            for jar in Path(tempfile.gettempdir()).glob("tmp*.kt.jar"):
                try:
                    jar.unlink(missing_ok=True)
                except OSError:
                    pass
        if available:
            engines.append("Kotlin parser")
            diagnostics.extend(
                line for line in found
                if re.search(r"error:.*(?:expecting|unexpected tokens|syntax|unclosed)", line, re.IGNORECASE)
            )

    if language == "rs" and shutil.which("rustc"):
        found, available = _run_source_tool(
            source_code,
            suffix=".rs",
            command_builder=lambda path: [
                shutil.which("rustc"), "--edition=2021", "--emit=metadata", "-o", f"{path}.rmeta", path,
            ],
            filename=filename,
            timeout=20,
        )
        if available:
            engines.append("Rust compiler")
            diagnostics.extend(line for line in found if re.search(r"(?:error(?:\[E\d+\])?|aborting due to)", line, re.IGNORECASE))

    if language == "cs":
        compiler = shutil.which("csc") or shutil.which("mcs")
        if compiler:
            found, available = _run_source_tool(
                source_code,
                suffix=".cs",
                command_builder=lambda path: [compiler, "-target:library", f"-out:{path}.dll", path],
                filename=filename,
                timeout=20,
            )
            if available:
                engines.append(f"{Path(compiler).name} compiler")
                diagnostics.extend(line for line in found if re.search(r"error CS\d+", line, re.IGNORECASE))

    return diagnostics, engines


def validate_source_syntax(source_code: str, language: str, filename: str) -> SyntaxValidation:
    """Parse supported source without execution and return evidence-bound diagnostics."""
    diagnostics: list[str] = []
    engines: list[str] = []

    tree_diagnostics, tree_available = _tree_sitter_diagnostics(source_code, language)
    if tree_available:
        engines.append("Tree-sitter grammar")
        diagnostics.extend(tree_diagnostics)

    if language == "css":
        engines.append("CSS declaration validator")
        diagnostics.extend(_css_diagnostics(source_code))
    elif language == "html":
        engines.append("HTML structure validator")
        diagnostics.extend(_html_diagnostics(source_code))
    else:
        engines.append("language-aware delimiter scanner")
        diagnostics.extend(_delimiter_diagnostics(source_code, language))
        if language == "sql":
            engines.append("SQL statement validator")
            diagnostics.extend(_sql_diagnostics(source_code))

    tool_diagnostics, tool_engines = _external_tool_diagnostics(source_code, language, filename)
    diagnostics.extend(tool_diagnostics)
    engines.extend(tool_engines)

    return _validation_result(language=language, diagnostics=diagnostics, engines=engines)

def professional_analysis_error(exc: Exception) -> str:
    message = str(exc).lower()
    if any(token in message for token in ("429", "quota", "resource_exhausted", "rate limit")):
        return "The analysis service is currently at capacity. Please wait a moment and run the review again."
    if any(token in message for token in ("api key", "permission", "unauthorized", "forbidden", "401", "403")):
        return "The analysis service is not configured correctly. Verify the server credentials and try again."
    if any(token in message for token in ("timeout", "timed out", "deadline")):
        return "The analysis took longer than expected. Large-source reviews may require additional processing time; please keep the page open and try again shortly."
    return "The analysis engine is temporarily unavailable. Please try again shortly."


def clean_filename(value: str) -> str:
    return (value or "uploaded-source.txt").replace("\\", "/").split("/")[-1][:255]


def validate_preferences(focus: str, detail: str) -> tuple[str, str]:
    normalized_focus = (focus or "balanced").lower()
    normalized_detail = (detail or "standard").lower()
    if normalized_focus not in SUPPORTED_FOCUS:
        raise HTTPException(status_code=422, detail="Select a supported review focus.")
    if normalized_detail not in SUPPORTED_DETAIL:
        raise HTTPException(status_code=422, detail="Select a supported analysis depth.")
    return normalized_focus, normalized_detail


def make_title(filename: str, source_code: str) -> str:
    """Use the first submitted file name as the permanent review/chat title."""
    del source_code  # The title must never be generated from source-code content.
    resolved = clean_filename(filename or "untitled-code.txt").strip()
    return (resolved or "untitled-code.txt")[:80]


def serialize_review(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "filename": row["filename"],
        "language": row["language"],
        "sourceCode": row["source_code"],
        "result": {
            "filename": row["filename"],
            "language": row["language"],
            "bug_report": row["bug_report"],
            "refactored_code": row["refactored_code"],
            "has_issues": bool(row["has_issues"]),
            "model_used": row["model_used"],
        },
        "explanation": row["explanation"] or "",
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def workspace_payload(client_id: str) -> dict:
    with db() as conn:
        workspace = conn.execute("SELECT * FROM workspaces WHERE client_id=?", (client_id,)).fetchone()
        rows = conn.execute(
            "SELECT * FROM reviews WHERE client_id=? ORDER BY updated_at DESC LIMIT 60",
            (client_id,),
        ).fetchall()
    avatar_url = None
    if workspace and (workspace["avatar_data"] or workspace["avatar_path"]):
        avatar_url = f"/api/profile/avatar?v={workspace['updated_at']}"
    return {
        "settings": {
            "profile": {
                "name": workspace["display_name"] if workspace else "",
                "role": workspace["professional_role"] if workspace else "",
                "avatarUrl": avatar_url,
            },
            "focus": workspace["focus"] if workspace else "balanced",
            "detail": workspace["detail"] if workspace else "standard",
            "autoExplain": bool(workspace["auto_explain"]) if workspace else False,
            "theme": workspace["theme"] if workspace else "dark",
        },
        "sessions": [serialize_review(row) for row in rows],
    }


@app.get("/api/health")
def health():
    return {"status": "ready", "capabilities": ["review", "correction", "explanation"]}


@app.get("/api/workspace")
def get_workspace(request: Request, response: Response):
    client_id = ensure_client(request, response)
    return workspace_payload(client_id)


@app.put("/api/settings")
def update_settings(payload: WorkspaceSettingsUpdate, request: Request, response: Response):
    client_id = ensure_client(request, response)
    if payload.theme not in SUPPORTED_THEME:
        raise HTTPException(status_code=422, detail="Select a supported appearance mode.")
    now = utc_now()
    with db() as conn:
        conn.execute(
            """
            UPDATE workspaces
            SET display_name=?, professional_role=?, focus=?, detail=?,
                auto_explain=?, theme=?, updated_at=?
            WHERE client_id=?
            """,
            (
                payload.profile.name.strip(),
                payload.profile.role.strip(),
                payload.focus,
                payload.detail,
                int(payload.auto_explain),
                payload.theme,
                now,
                client_id,
            ),
        )
    return workspace_payload(client_id)["settings"]


@app.post("/api/profile/avatar")
async def upload_avatar(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
):
    client_id = ensure_client(request, response)
    content_type = (file.content_type or "").lower()
    extension_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }
    extension = extension_map.get(content_type)
    if not extension:
        raise HTTPException(status_code=422, detail="Upload a PNG, JPG, or WebP profile image.")
    data = await file.read(MAX_AVATAR_BYTES + 1)
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="Profile images must be 5 MB or smaller.")
    if len(data) < 32:
        raise HTTPException(status_code=422, detail="The selected image is not valid.")

    now = utc_now()
    with db() as conn:
        conn.execute(
            """
            UPDATE workspaces
            SET avatar_data=?, avatar_mime=?, avatar_path=NULL, updated_at=?
            WHERE client_id=?
            """,
            (data, content_type, now, client_id),
        )
    return {"avatarUrl": f"/api/profile/avatar?v={now}"}


@app.get("/api/profile/avatar")
def read_avatar(request: Request, response: Response):
    client_id = ensure_client(request, response)
    with db() as conn:
        row = conn.execute(
            "SELECT avatar_data, avatar_mime, avatar_path FROM workspaces WHERE client_id=?",
            (client_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No profile image is available.")

    if row["avatar_data"]:
        return Response(
            content=bytes(row["avatar_data"]),
            media_type=row["avatar_mime"] or "application/octet-stream",
            headers={"Cache-Control": "private, max-age=31536000, immutable"},
        )

    # Read-only compatibility for an older installation until its avatar is migrated.
    if row["avatar_path"]:
        path = Path(row["avatar_path"])
        if path.is_file():
            return FileResponse(path, headers={"Cache-Control": "private, max-age=31536000, immutable"})
    raise HTTPException(status_code=404, detail="No profile image is available.")


@app.delete("/api/reviews")
def clear_reviews(request: Request, response: Response):
    client_id = ensure_client(request, response)
    with db() as conn:
        conn.execute("DELETE FROM reviews WHERE client_id=?", (client_id,))
    return {"cleared": True}


def previously_verified_source(
    *, client_id: str, source_code: str, language: str
) -> Optional[sqlite3.Row]:
    """Return a prior trusted review for byte-identical source.

    A previously clean submission is stable across repeat reviews. A previously
    corrected output is trusted only when it differs from its original source,
    preventing failed/no-op correction attempts from being treated as verified.
    """
    with db() as conn:
        return conn.execute(
            """
            SELECT id, source_code, refactored_code, has_issues, bug_report, updated_at
            FROM reviews
            WHERE client_id=?
              AND language=?
              AND (
                    (has_issues=0 AND source_code=?)
                 OR (has_issues=1 AND refactored_code=? AND refactored_code<>source_code)
              )
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (client_id, language, source_code, source_code),
        ).fetchone()


@app.post("/api/review")
async def review(
    request: Request,
    response: Response,
    file: Optional[UploadFile] = File(None),
    code: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
    focus: str = Form("balanced"),
    detail: str = Form("standard"),
):
    """Review source input and persist the validated session for this device workspace."""
    client_id = ensure_client(request, response)
    resolved_focus, resolved_detail = validate_preferences(focus, detail)

    if file is not None:
        raw_bytes = await file.read(settings.MAX_CODE_CHARS * 4 + 1)
        if len(raw_bytes) > settings.MAX_CODE_CHARS * 4:
            raise HTTPException(status_code=413, detail="This source file exceeds the supported review size.")
        try:
            source_code = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail="This file is not readable source text. Upload a UTF-8 encoded code file.",
            ) from exc
        resolved_filename = clean_filename(file.filename or "uploaded-source.txt")
    elif code is not None:
        source_code = code
        resolved_filename = clean_filename(filename or f"snippet.{language or 'txt'}")
    else:
        raise HTTPException(status_code=422, detail="Attach a source file or paste code to begin the review.")

    if not source_code.strip():
        raise HTTPException(status_code=422, detail="The submitted source is empty.")
    if len(source_code) > settings.MAX_CODE_CHARS:
        raise HTTPException(status_code=413, detail=f"This review exceeds the {settings.MAX_CODE_CHARS:,}-character limit.")

    resolution = resolve_submission_language(
        source_code,
        resolved_filename,
        language,
        uploaded_file=file is not None,
    )
    resolved_language = resolution.language
    resolved_filename = resolution.filename
    syntax_validation = validate_source_syntax(source_code, resolved_language, resolved_filename)

    prior_verified = previously_verified_source(
        client_id=client_id,
        source_code=source_code,
        language=resolved_language,
    )

    try:
        if prior_verified and syntax_validation.status != "failed":
            result = {
                "bug_report": "- **Info** This exact source has already passed CodeFix AI verification. No confirmed defects were found.",
                "refactored_code": source_code,
                "has_issues": False,
                "verification_status": "repeat-source-verified-clean",
            }
        else:
            result = review_code(
                code=source_code,
                language=resolved_language,
                filename=resolved_filename,
                focus=resolved_focus,
                detail=resolved_detail,
                syntax_context=syntax_validation.summary,
                syntax_status=syntax_validation.status,
            )

        # Never return a correction that still fails the available language parser/compiler.
        # Two focused repair passes use fresh deterministic evidence from the proposed output.
        if result["has_issues"]:
            corrected_validation = validate_source_syntax(
                result["refactored_code"], resolved_language, resolved_filename
            )
            repair_attempt = 0
            while corrected_validation.status == "failed" and repair_attempt < 2:
                result["refactored_code"] = repair_code(
                    original_code=source_code,
                    candidate_code=result["refactored_code"],
                    language=resolved_language,
                    filename=resolved_filename,
                    bug_report=result["bug_report"],
                    validation_context=corrected_validation.summary,
                )
                repair_attempt += 1
                corrected_validation = validate_source_syntax(
                    result["refactored_code"], resolved_language, resolved_filename
                )
            if corrected_validation.status == "failed":
                # Do not discard a valid review because a model-proposed edit failed final parsing.
                # Preserve the submitted source, retain the proven findings, and mark the correction as unverified.
                result["refactored_code"] = source_code
                verification_note = (
                    "- **Warning** The proposed correction could not be validated safely, so the original "
                    "source is preserved in the corrected-code panel. Review the confirmed finding before applying changes."
                )
                if verification_note not in result["bug_report"]:
                    result["bug_report"] = result["bug_report"].rstrip() + "\n" + verification_note
                result["verification_status"] = "findings-verified-correction-preserved"
    except GeminiParsingError as exc:
        if syntax_validation.status == "failed":
            result = {
                "bug_report": f"- **Critical** {syntax_validation.summary}",
                "refactored_code": source_code,
                "has_issues": True,
                "verification_status": "deterministic-fallback",
            }
        else:
            # Never mislabel a non-Python file as verified clean merely because an AI
            # response was malformed. Surface a retryable service error instead.
            raise HTTPException(
                status_code=503,
                detail=(
                    "The polyglot analysis response could not be verified safely. "
                    "Your source was not modified; please run the review again."
                ),
            ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=professional_analysis_error(exc)) from exc

    now = utc_now()
    session_id = str(uuid.uuid4())
    title = make_title(resolved_filename, source_code)
    with db() as conn:
        conn.execute(
            """
            INSERT INTO reviews(
                id, client_id, title, filename, language, source_code,
                bug_report, refactored_code, has_issues, model_used,
                explanation, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                session_id,
                client_id,
                title,
                resolved_filename,
                resolved_language,
                source_code,
                result["bug_report"],
                result["refactored_code"],
                int(result["has_issues"]),
                settings.GEMINI_MODEL,
                "",
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM reviews WHERE id=?", (session_id,)).fetchone()
    return {"session": serialize_review(row)}


@app.post("/api/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest, request: Request, response: Response):
    """Generate a line-aware walkthrough and persist it to the selected review session."""
    client_id = ensure_client(request, response)
    if not payload.code.strip():
        raise HTTPException(status_code=422, detail="The code selected for explanation is empty.")
    try:
        explanation = explain_code(
            code=payload.code,
            language=payload.language,
            filename=payload.filename,
            detail=payload.detail,
        )
    except GeminiParsingError as exc:
        raise HTTPException(status_code=502, detail="CodeFix AI could not verify the code walkthrough. Please try again.") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=professional_analysis_error(exc)) from exc

    if payload.session_id:
        with db() as conn:
            conn.execute(
                "UPDATE reviews SET explanation=?, updated_at=? WHERE id=? AND client_id=?",
                (explanation, utc_now(), payload.session_id, client_id),
            )

    return ExplainResponse(
        filename=payload.filename,
        language=payload.language,
        explanation=explanation,
        model_used=settings.GEMINI_MODEL,
    )
