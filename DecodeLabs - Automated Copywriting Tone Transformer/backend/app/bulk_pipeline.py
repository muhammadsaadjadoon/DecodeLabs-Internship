"""
Bulk CSV pipeline for Lexora.

Adds user-friendly CSV validation: missing columns, encoding problems, empty
fields, duplicate row warnings, unexpected columns, and row-level failures.
"""
from __future__ import annotations

import asyncio
import csv
import io
import logging
from collections import Counter

from app.gemini_client import GeminiPermanentError, GeminiTransientError, generate_copy
from app.models import (
    BulkResult,
    BulkRow,
    CTAType,
    ContentObjective,
    CopyLength,
    EmojiLevel,
    FormalityLevel,
    GenerationRequest,
    GenerationResponse,
    Platform,
    Tone,
)
from app.prompt_engine import compile_master_template

logger = logging.getLogger("bulk_pipeline")

REQUIRED_COLUMNS = {"product_name", "product_description", "platform", "tone"}
OPTIONAL_COLUMNS = {
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
    "temperature",
    "top_p",
}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


class CSVValidationError(ValueError):
    pass


def _enum_or_default(enum_cls, value: str | None, default):
    cleaned = (value or "").strip().lower()
    if not cleaned:
        return default
    try:
        return enum_cls(cleaned)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_cls)
        raise CSVValidationError(f"Invalid value '{value}' for {enum_cls.__name__}. Allowed: {allowed}") from exc


def _float_or_default(value: str | None, default: float, label: str, min_value: float, max_value: float) -> float:
    if value is None or str(value).strip() == "":
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise CSVValidationError(f"{label} must be a number") from exc
    if not min_value <= parsed <= max_value:
        raise CSVValidationError(f"{label} must be between {min_value} and {max_value}")
    return parsed


def _int_or_default(value: str | None, default: int, label: str, min_value: int, max_value: int) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise CSVValidationError(f"{label} must be a whole number") from exc
    if not min_value <= parsed <= max_value:
        raise CSVValidationError(f"{label} must be between {min_value} and {max_value}")
    return parsed


def parse_csv(raw_bytes: bytes) -> list[BulkRow]:
    if not raw_bytes:
        raise CSVValidationError("CSV file is empty")
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVValidationError("CSV encoding is invalid. Please save the file as UTF-8 CSV.") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise CSVValidationError("CSV header row is missing")

    fieldnames = {field.strip() for field in reader.fieldnames if field}
    missing = sorted(REQUIRED_COLUMNS - fieldnames)
    if missing:
        raise CSVValidationError(f"Missing required columns: {', '.join(missing)}")

    unexpected = sorted(fieldnames - ALL_COLUMNS)
    if unexpected:
        logger.warning("CSV contains unexpected columns: %s", unexpected)

    rows: list[BulkRow] = []
    seen_keys: Counter[tuple[str, str, str, str]] = Counter()
    for i, raw_row in enumerate(reader, start=1):
        row = {key: (value or "").strip() for key, value in raw_row.items() if key}
        if not any(row.values()):
            continue
        for required in REQUIRED_COLUMNS:
            if not row.get(required):
                raise CSVValidationError(f"Row {i}: '{required}' is required")

        key = (
            row["product_name"].lower(),
            row["product_description"].lower(),
            row["platform"].lower(),
            row["tone"].lower(),
        )
        seen_keys[key] += 1
        if seen_keys[key] > 1:
            logger.warning("Duplicate CSV row detected at row %s for product %s", i, row["product_name"])

        try:
            rows.append(
                BulkRow(
                    row_id=i,
                    product_name=row["product_name"],
                    product_description=row["product_description"],
                    target_audience=row.get("target_audience") or "General buyers",
                    content_objective=_enum_or_default(ContentObjective, row.get("content_objective"), ContentObjective.SALES),
                    language=row.get("language") or "English",
                    copy_length=_enum_or_default(CopyLength, row.get("copy_length"), CopyLength.MEDIUM),
                    keywords=row.get("keywords") or "",
                    brand_voice=row.get("brand_voice") or "",
                    emoji_level=_enum_or_default(EmojiLevel, row.get("emoji_level"), EmojiLevel.LOW),
                    number_of_variations=_int_or_default(row.get("number_of_variations"), 3, "number_of_variations", 1, 5),
                    formality_level=_enum_or_default(FormalityLevel, row.get("formality_level"), FormalityLevel.BALANCED),
                    cta_type=_enum_or_default(CTAType, row.get("cta_type"), CTAType.LEARN_MORE),
                    platform=_enum_or_default(Platform, row.get("platform"), Platform.LINKEDIN),
                    tone=_enum_or_default(Tone, row.get("tone"), Tone.PROFESSIONAL),
                    temperature=_float_or_default(row.get("temperature"), 0.7, "temperature", 0.0, 2.0),
                    top_p=_float_or_default(row.get("top_p"), 0.9, "top_p", 0.0, 1.0),
                )
            )
        except CSVValidationError as exc:
            raise CSVValidationError(f"Row {i}: {exc}") from exc
    return rows


async def _process_row(row: BulkRow) -> BulkResult:
    try:
        request = GenerationRequest(
            product_name=row.product_name,
            product_description=row.product_description,
            target_audience=row.target_audience,
            content_objective=row.content_objective,
            language=row.language,
            copy_length=row.copy_length,
            keywords=row.keywords,
            brand_voice=row.brand_voice,
            emoji_level=row.emoji_level,
            number_of_variations=row.number_of_variations,
            formality_level=row.formality_level,
            cta_type=row.cta_type,
            platform=row.platform,
            tone=row.tone,
            temperature=row.temperature,
            top_p=row.top_p,
        )
        prompt = compile_master_template(request)
        copy = await generate_copy(prompt, request.temperature, request.top_p)
        response = GenerationResponse.build(request, copy)
        return BulkResult(row_id=row.row_id, product_name=row.product_name, status="success", response=response)
    except (GeminiPermanentError, GeminiTransientError, Exception) as exc:
        logger.error("Row %s failed: %s", row.row_id, exc)
        return BulkResult(row_id=row.row_id, product_name=row.product_name, status="error", error=str(exc))


async def run_bulk_job(rows: list[BulkRow]) -> list[BulkResult]:
    tasks = [_process_row(row) for row in rows]
    return await asyncio.gather(*tasks, return_exceptions=False)
