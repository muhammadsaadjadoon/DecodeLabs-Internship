from __future__ import annotations

import base64
import hashlib
import json
import mmap
import os
import re
import tempfile
from dataclasses import dataclass, asdict
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Optional

import requests
from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

MAX_PROVIDER_JSON_BYTES = int(os.getenv("MAX_PROVIDER_JSON_BYTES", str(64 * 1024 * 1024)))
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", str(40 * 1024 * 1024)))
AESTHETIC_THRESHOLD = float(os.getenv("AESTHETIC_THRESHOLD", "7.0"))
SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", "0.58"))
QA_ENABLED = os.getenv("QA_ENABLED", "true").lower() == "true"
QA_ENFORCE = os.getenv("QA_ENFORCE", "true").lower() == "true"
OUTPUT_MODERATION_ENABLED = os.getenv("OUTPUT_MODERATION_ENABLED", "true").lower() == "true"


@dataclass
class SafetyDecision:
    allowed: bool
    code: str
    message: str
    categories: list[str]


@dataclass
class QualityReport:
    available: bool
    method: str
    safe: Optional[bool]
    safety_status: str
    safety_reason: str
    aesthetic_score: Optional[float]
    semantic_score: Optional[float]
    passed: Optional[bool]
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidatedImage:
    temp_path: Path
    mime_type: str
    extension: str
    width: int
    height: int
    source_width: int
    source_height: int
    requested_width: int
    requested_height: int
    dimension_match: bool
    dimension_adjusted: bool
    dimension_warning: str
    sha256: str
    size_bytes: int


_INPUT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("explicit sexual content", re.compile(r"\b(?:nude|naked|without\s+(?:a\s+)?dress|without\s+clothes?|undressed|porn(?:ographic)?|explicit\s+sex|sexual\s+act|genitals?|nipples?)\b", re.I)),
    ("sexual content involving minors", re.compile(r"\b(?:child|minor|underage|young\s+girl|young\s+boy|teen)\b[\s\S]{0,80}\b(?:nude|naked|sexual|explicit|porn)\b", re.I)),
    ("graphic violence", re.compile(r"\b(?:graphic\s+gore|dismember(?:ed|ment)?|decapitat(?:e|ed|ion)|visible\s+organs?|extreme\s+gore)\b", re.I)),
    ("self-harm", re.compile(r"\b(?:suicide|self[-\s]?harm|cutting\s+myself|kill\s+myself)\b", re.I)),
    ("hateful abuse", re.compile(r"\b(?:exterminate|genocide|lynch)\b[\s\S]{0,60}\b(?:race|religion|ethnic|people|group)\b", re.I)),
)


def moderate_input_text(text: str) -> SafetyDecision:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    categories = [label for label, pattern in _INPUT_RULES if pattern.search(normalized)]
    if categories:
        return SafetyDecision(
            allowed=False,
            code="INPUT_SAFETY_REJECTED",
            message="Prismora cannot create explicit, exploitative, graphically violent, hateful, or self-harm content. Please revise the creative direction.",
            categories=categories,
        )
    return SafetyDecision(True, "INPUT_SAFETY_PASSED", "Prompt safety check passed.", [])


def _new_temp_path(temp_dir: Path, suffix: str) -> Path:
    temp_dir.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="prismora_", suffix=suffix, dir=temp_dir)
    os.close(fd)
    return Path(name)


def _write_stream_to_file(chunks: Iterable[bytes], destination: Path, max_bytes: int) -> int:
    size = 0
    with destination.open("wb") as output:
        for chunk in chunks:
            if not chunk:
                continue
            size += len(chunk)
            if size > max_bytes:
                raise RuntimeError("The generated visual exceeded the supported size limit.")
            output.write(chunk)
    return size


def stream_response_to_temp(response: requests.Response, temp_dir: Path) -> Path:
    content_type = (response.headers.get("content-type") or "").lower()
    if content_type.startswith("image/"):
        suffix = ".jpg" if "jpeg" in content_type else ".png"
        image_path = _new_temp_path(temp_dir, suffix)
        try:
            _write_stream_to_file(response.iter_content(chunk_size=65536), image_path, MAX_IMAGE_BYTES)
            return image_path
        except Exception:
            image_path.unlink(missing_ok=True)
            raise

    json_path = _new_temp_path(temp_dir, ".json")
    try:
        _write_stream_to_file(response.iter_content(chunk_size=65536), json_path, MAX_PROVIDER_JSON_BYTES)
        return extract_asset_from_json_file(json_path, temp_dir)
    finally:
        json_path.unlink(missing_ok=True)


def _find_json_string(mm: mmap.mmap, keys: tuple[bytes, ...]) -> tuple[int, int] | None:
    for key in keys:
        pattern = re.compile(rb'"' + re.escape(key) + rb'"\s*:\s*"')
        match = pattern.search(mm)
        if not match:
            continue
        start = match.end()
        pos = start
        escaped = False
        while pos < len(mm):
            byte = mm[pos]
            if byte == 92 and not escaped:  # backslash
                escaped = True
                pos += 1
                continue
            if byte == 34 and not escaped:  # quote
                return start, pos
            escaped = False
            pos += 1
    return None


def _decode_base64_range(mm: mmap.mmap, start: int, end: int, destination: Path) -> None:
    first = bytes(mm[start:min(end, start + 256)])
    prefix_skip = 0
    if first.startswith(b"data:image") and b"," in first:
        prefix_skip = first.index(b",") + 1
    cursor = start + prefix_skip
    carry = b""
    written = 0
    with destination.open("wb") as output:
        while cursor < end:
            block = bytes(mm[cursor:min(end, cursor + 262144)])
            cursor += len(block)
            block = re.sub(rb"\s+", b"", block)
            data = carry + block
            usable = len(data) - (len(data) % 4)
            if usable:
                decoded = base64.b64decode(data[:usable], validate=False)
                written += len(decoded)
                if written > MAX_IMAGE_BYTES:
                    raise RuntimeError("The generated visual exceeded the supported size limit.")
                output.write(decoded)
            carry = data[usable:]
        if carry:
            decoded = base64.b64decode(carry, validate=False)
            written += len(decoded)
            if written > MAX_IMAGE_BYTES:
                raise RuntimeError("The generated visual exceeded the supported size limit.")
            output.write(decoded)


def _download_url_to_temp(url: str, temp_dir: Path) -> Path:
    destination = _new_temp_path(temp_dir, ".img")
    try:
        with requests.get(url, stream=True, timeout=(3.05, 75)) as response:
            response.raise_for_status()
            _write_stream_to_file(response.iter_content(chunk_size=65536), destination, MAX_IMAGE_BYTES)
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def extract_asset_from_json_file(json_path: Path, temp_dir: Path) -> Path:
    with json_path.open("rb") as source, mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        url_range = _find_json_string(mm, (b"url", b"image_url"))
        if url_range:
            raw_url = bytes(mm[url_range[0]:url_range[1]])
            url = raw_url.decode("utf-8", errors="strict").replace("\\/", "/")
            if url.startswith("http"):
                return _download_url_to_temp(url, temp_dir)

        image_range = _find_json_string(mm, (b"image", b"b64_json", b"base64", b"result"))
        if image_range:
            destination = _new_temp_path(temp_dir, ".img")
            try:
                _decode_base64_range(mm, image_range[0], image_range[1], destination)
                return destination
            except Exception:
                destination.unlink(missing_ok=True)
                raise
    raise RuntimeError("The image service returned an unsupported result.")


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def validate_and_normalize_image(source_path: Path, requested_width: int, requested_height: int, temp_dir: Path) -> ValidatedImage:
    normalized_path = _new_temp_path(temp_dir, ".png")
    try:
        with Image.open(source_path) as probe:
            source_width, source_height = probe.size
            probe.verify()
        with Image.open(source_path) as decoded:
            decoded = ImageOps.exif_transpose(decoded)
            decoded.load()  # Required pixel-level decode catches truncated streams.
            source_width, source_height = decoded.size
            dimension_match = (source_width, source_height) == (requested_width, requested_height)
            dimension_adjusted = not dimension_match
            if dimension_adjusted:
                canvas = ImageOps.fit(
                    decoded.convert("RGB"),
                    (requested_width, requested_height),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
            else:
                canvas = decoded.convert("RGB")
            canvas.save(normalized_path, format="PNG", optimize=True)
        digest, size_bytes = _hash_file(normalized_path)
        warning = ""
        if dimension_adjusted:
            warning = (
                f"The image engine returned {source_width}×{source_height}; Prismora normalized the final asset "
                f"to the requested {requested_width}×{requested_height} canvas."
            )
        return ValidatedImage(
            temp_path=normalized_path,
            mime_type="image/png",
            extension=".png",
            width=requested_width,
            height=requested_height,
            source_width=source_width,
            source_height=source_height,
            requested_width=requested_width,
            requested_height=requested_height,
            dimension_match=dimension_match,
            dimension_adjusted=dimension_adjusted,
            dimension_warning=warning,
            sha256=digest,
            size_bytes=size_bytes,
        )
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        normalized_path.unlink(missing_ok=True)
        raise RuntimeError("The generated visual could not be fully decoded and validated.") from exc
    finally:
        source_path.unlink(missing_ok=True)


def _heuristic_aesthetic_score(image_path: Path) -> float:
    with Image.open(image_path) as image:
        thumb = ImageOps.fit(image.convert("RGB"), (384, 384), method=Image.Resampling.LANCZOS)
        gray = thumb.convert("L")
        stats = ImageStat.Stat(gray)
        contrast = min(1.0, (stats.stddev[0] or 0.0) / 64.0)
        entropy = min(1.0, gray.entropy() / 8.0)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_std = ImageStat.Stat(edges).stddev[0]
        sharpness = min(1.0, edge_std / 48.0)
        score = 3.6 + 2.1 * contrast + 2.2 * entropy + 2.1 * sharpness
        return round(max(0.0, min(10.0, score)), 2)


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object returned")
    return json.loads(cleaned[start:end + 1])


def run_visual_quality_review(
    image_path: Path,
    prompt: str,
    gemini_api_key: str,
    gemini_model: str,
) -> QualityReport:
    heuristic_score = _heuristic_aesthetic_score(image_path)
    if not QA_ENABLED:
        return QualityReport(False, "disabled", None, "not_checked", "", heuristic_score, None, None, "Automated review is disabled.")
    if not gemini_api_key:
        return QualityReport(
            False,
            "pixel-quality-fallback",
            None,
            "not_checked",
            "AI visual safety review is unavailable because no vision reviewer is configured.",
            heuristic_score,
            None,
            None,
            "File integrity and visual-quality heuristics passed; semantic alignment was not scored.",
        )

    with Image.open(image_path) as image:
        preview = image.convert("RGB")
        preview.thumbnail((768, 768), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        preview.save(buffer, format="JPEG", quality=88, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    instruction = f"""
You are Prismora Visual Quality Assurance. Review the attached generated image against the requested prompt.
Return one strict JSON object only with these keys:
{{
  "safe": true,
  "safety_reason": "",
  "aesthetic_score": 0.0,
  "semantic_score": 0.0,
  "notes": ""
}}
Scoring rules:
- aesthetic_score: 0 to 10 for composition, lighting, coherence, anatomy/material quality, detail and visual polish.
- semantic_score: 0 to 1 for how accurately the image matches the subject, count, action, relationships, colors, objects and setting in the prompt.
- safe must be false for explicit sexual content, sexualized minors, graphic gore, hateful abuse or self-harm imagery.
Requested prompt: {prompt[:1800]}
""".strip()
    body = {
        "contents": [{"role": "user", "parts": [
            {"text": instruction},
            {"inlineData": {"mimeType": "image/jpeg", "data": encoded}},
        ]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 500, "responseMimeType": "application/json"},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_api_key}"
    try:
        response = requests.post(url, json=body, timeout=(3.05, 45))
        response.raise_for_status()
        data = response.json()
        result = _parse_json_object(data["candidates"][0]["content"]["parts"][0]["text"])
        safe = bool(result.get("safe", True))
        aesthetic = round(max(0.0, min(10.0, float(result.get("aesthetic_score", heuristic_score)))), 2)
        semantic = round(max(0.0, min(1.0, float(result.get("semantic_score", 0.0)))), 3)
        passed = safe and aesthetic >= AESTHETIC_THRESHOLD and semantic >= SEMANTIC_THRESHOLD
        return QualityReport(
            True,
            "gemini-vision-qa",
            safe,
            "passed" if safe else "rejected",
            str(result.get("safety_reason") or ""),
            aesthetic,
            semantic,
            passed,
            str(result.get("notes") or ""),
        )
    except Exception as exc:
        return QualityReport(
            False,
            "pixel-quality-fallback",
            None,
            "not_checked",
            "AI visual review was temporarily unavailable.",
            heuristic_score,
            None,
            None,
            f"File integrity and aesthetic heuristics completed; semantic alignment was not scored ({type(exc).__name__}).",
        )


def should_reject_for_quality(report: QualityReport) -> bool:
    return bool(QA_ENFORCE and report.available and report.passed is False)


def should_reject_for_output_safety(report: QualityReport) -> bool:
    return bool(OUTPUT_MODERATION_ENABLED and report.available and report.safe is False)
