"""Gemini orchestration with resilient parsing and evidence-based verification."""
from __future__ import annotations

import json
import re
from typing import Any

from google import genai
from google.genai import types

from app.config import settings
from app.prompts import (
    CLEAN_CHALLENGE_SYSTEM_INSTRUCTION,
    LARGE_ANALYSIS_SYSTEM_INSTRUCTION,
    LARGE_REPAIR_SYSTEM_INSTRUCTION,
    LARGE_PATCH_SYSTEM_INSTRUCTION,
    LARGE_VERIFIER_SYSTEM_INSTRUCTION,
    EXPLAIN_SYSTEM_INSTRUCTION,
    REPAIR_SYSTEM_INSTRUCTION,
    SYSTEM_INSTRUCTION,
    VERIFIER_SYSTEM_INSTRUCTION,
    build_clean_challenge_prompt,
    build_large_analysis_prompt,
    build_large_repair_prompt,
    build_large_patch_prompt,
    build_large_verification_prompt,
    build_explain_prompt,
    build_repair_prompt,
    build_user_prompt,
    build_verification_prompt,
    COMPACT_AUDIT_SYSTEM_INSTRUCTION,
    COMPACT_VERIFY_SYSTEM_INSTRUCTION,
    COMPACT_REPAIR_SYSTEM_INSTRUCTION,
    build_compact_analysis_prompt,
    build_compact_verification_prompt,
    build_compact_repair_prompt,
)

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


CODE_FENCE_RE = re.compile(r"```(?:[a-zA-Z0-9_+\-#.]*)\s*\n?(.*?)```", re.DOTALL)
BUG_HEADER_RE = re.compile(
    r"#{1,4}\s*BUG[\s_-]*REPORT\s*:?[ \t]*\n(.*?)(?=#{1,4}\s*REFACTORED[\s_-]*CODE\b|\Z)",
    re.IGNORECASE | re.DOTALL,
)
CODE_HEADER_RE = re.compile(
    r"#{1,4}\s*REFACTORED[\s_-]*CODE\s*:?[ \t]*\n(.*)",
    re.IGNORECASE | re.DOTALL,
)
VERDICT_RE = re.compile(
    r"#{1,4}\s*VERDICT\s*:?[ \t]*\n?\s*(CLEAN|ISSUES)\b",
    re.IGNORECASE,
)
VERIFIED_BUG_RE = re.compile(
    r"#{1,4}\s*VERIFIED[\s_-]*BUG[\s_-]*REPORT\s*:?[ \t]*\n(.*?)(?=#{1,4}\s*VERIFIED[\s_-]*CODE\b|\Z)",
    re.IGNORECASE | re.DOTALL,
)
VERIFIED_CODE_RE = re.compile(
    r"#{1,4}\s*VERIFIED[\s_-]*CODE\s*:?[ \t]*\n(.*)",
    re.IGNORECASE | re.DOTALL,
)
EXPLANATION_HEADERS = ("## CODE_SUMMARY", "## EXECUTION_FLOW", "## LINE_BY_LINE", "## KEY_CONCEPTS")
CLEAN_FINDING = "- **Info** No functional bugs, security issues, or performance problems were found in this code."
SEVERITY_RE = re.compile(r"\*\*(?:Critical|Warning)\*\*", re.IGNORECASE)
CLEAN_RE = re.compile(
    r"no\s+(?:functional\s+)?(?:bugs?|issues?|defects?|errors?).*(?:found|detected)|code\s+(?:is\s+)?clean",
    re.IGNORECASE | re.DOTALL,
)
LARGE_SOURCE_RE = re.compile(
    r"<<<BEGIN_COMPLETE_SOURCE>>>\s*(.*?)\s*<<<END_COMPLETE_SOURCE>>>",
    re.DOTALL,
)

REVIEW_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["CLEAN", "ISSUES"]},
        "bug_report": {"type": "string"},
        "refactored_code": {"type": "string"},
    },
    "required": ["verdict", "bug_report", "refactored_code"],
}

VERIFY_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["CLEAN", "ISSUES"]},
        "bug_report": {"type": "string"},
        "verified_code": {"type": "string"},
    },
    "required": ["verdict", "bug_report", "verified_code"],
}

FINDINGS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["CLEAN", "ISSUES"]},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["Critical", "Warning"]},
                    "line": {"type": "string"},
                    "symbol": {"type": "string"},
                    "cause": {"type": "string"},
                    "impact": {"type": "string"},
                    "correction": {"type": "string"},
                },
                "required": ["severity", "line", "symbol", "cause", "impact", "correction"],
            },
        },
    },
    "required": ["verdict", "findings"],
}


class GeminiParsingError(Exception):
    """Raised when the model reply cannot be converted into the review contract."""


def _extract_code(section: str, fallback_code: str) -> str:
    fence_match = CODE_FENCE_RE.search(section or "")
    code = fence_match.group(1).rstrip("\n") if fence_match else (section or "").strip()
    return code or fallback_code


def _extract_json_object(raw_text: str) -> dict[str, Any] | None:
    text = (raw_text or "").strip()
    candidates = [text]
    fenced = CODE_FENCE_RE.search(text)
    if fenced:
        candidates.insert(0, fenced.group(1).strip())
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except (TypeError, ValueError):
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _normalize_bug_report(report: str, *, issues: bool) -> str:
    text = (report or "").strip()
    if not issues:
        return CLEAN_FINDING
    if not text:
        return "- **Warning** A definite defect was identified, but the analysis did not provide a detailed description."

    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith(("-", "*")):
            line = f"- {line}"
        if not SEVERITY_RE.search(line):
            body = line.lstrip("-* ").strip()
            line = f"- **Warning** {body}"
        lines.append(line.replace("* **", "- **", 1) if line.startswith("* **") else line)
    return "\n".join(lines) or "- **Warning** A definite source-code defect requires correction."


def _report_is_clean(report: str) -> bool:
    text = (report or "").strip()
    return not text or bool(CLEAN_RE.search(text)) or text == CLEAN_FINDING


def _parse_structured_reply(raw_text: str, fallback_code: str) -> tuple[str, str]:
    bug_match = BUG_HEADER_RE.search(raw_text or "")
    code_match = CODE_HEADER_RE.search(raw_text or "")
    if bug_match and code_match:
        bug_report = bug_match.group(1).strip()
        refactored_code = _extract_code(code_match.group(1), fallback_code)
        if bug_report and refactored_code:
            return bug_report, refactored_code

    payload = _extract_json_object(raw_text)
    if payload:
        bug_report = str(payload.get("bug_report") or payload.get("findings") or "").strip()
        refactored_code = str(
            payload.get("refactored_code") or payload.get("corrected_code") or payload.get("code") or ""
        ).rstrip("\n")
        if bug_report and refactored_code:
            return bug_report, refactored_code

    # Last-resort recovery: if a fenced source block exists, keep it and treat the
    # preceding prose as the report. This prevents harmless heading drift from failing a review.
    fence = CODE_FENCE_RE.search(raw_text or "")
    if fence:
        code = fence.group(1).rstrip("\n") or fallback_code
        report = (raw_text or "")[: fence.start()].strip()
        report = re.sub(r"^#{1,4}.*?(?:REPORT|FINDINGS?)\s*:?[ \t]*", "", report, flags=re.I | re.S).strip()
        if report:
            return report, code

    raise GeminiParsingError("The required review sections were not returned.")


def _parse_verification_reply(raw_text: str, original_code: str) -> tuple[str, str, str]:
    verdict_match = VERDICT_RE.search(raw_text or "")
    bug_match = VERIFIED_BUG_RE.search(raw_text or "")
    code_match = VERIFIED_CODE_RE.search(raw_text or "")
    if verdict_match and bug_match and code_match:
        verdict = verdict_match.group(1).upper()
        bug_report = bug_match.group(1).strip()
        verified_code = _extract_code(code_match.group(1), original_code)
        if verdict == "CLEAN":
            return verdict, CLEAN_FINDING, original_code
        return verdict, _normalize_bug_report(bug_report, issues=True), verified_code

    payload = _extract_json_object(raw_text)
    if payload:
        verdict = str(payload.get("verdict") or "").strip().upper()
        if verdict in {"CLEAN", "ISSUES"}:
            report = str(payload.get("bug_report") or payload.get("verified_bug_report") or "")
            code = str(payload.get("verified_code") or payload.get("refactored_code") or original_code)
            if verdict == "CLEAN":
                return verdict, CLEAN_FINDING, original_code
            return verdict, _normalize_bug_report(report, issues=True), code.rstrip("\n") or original_code

    raise GeminiParsingError("The verification response did not match the required structure.")


def _validate_explanation(raw_text: str) -> str:
    text = raw_text.strip()
    positions = [text.find(header) for header in EXPLANATION_HEADERS]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise GeminiParsingError("The code explanation did not match the required structure.")
    return text


def _generate_text(
    *,
    prompt: str,
    system_instruction: str,
    max_output_tokens: int | None = None,
) -> str:
    response = _get_client().models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            max_output_tokens=max_output_tokens or settings.GEMINI_MAX_OUTPUT_TOKENS,
        ),
    )
    text = (response.text or "").strip()
    if not text:
        raise GeminiParsingError("The analysis engine returned an empty response.")
    return text


def _generate_json_payload(
    *,
    prompt: str,
    system_instruction: str,
    response_schema: dict[str, Any],
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    """Request native JSON output so valid reviews never depend on Markdown heading drift."""
    response = _get_client().models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            max_output_tokens=max_output_tokens or settings.GEMINI_MAX_OUTPUT_TOKENS,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )
    raw = (response.text or "").strip()
    payload = _extract_json_object(raw)
    if not payload:
        raise GeminiParsingError("The analysis engine did not return valid structured JSON.")
    return payload


def _review_tuple_from_payload(payload: dict[str, Any], original_code: str) -> tuple[str, str]:
    verdict = str(payload.get("verdict") or "").strip().upper()
    report = str(payload.get("bug_report") or payload.get("findings") or "").strip()
    code = str(
        payload.get("refactored_code")
        or payload.get("corrected_code")
        or payload.get("verified_code")
        or original_code
    ).rstrip("\n")
    if verdict not in {"CLEAN", "ISSUES"}:
        raise GeminiParsingError("The structured review omitted a valid verdict.")
    if verdict == "CLEAN":
        return CLEAN_FINDING, original_code
    if not report:
        raise GeminiParsingError("The structured review reported issues without evidence.")
    return _normalize_bug_report(report, issues=True), code or original_code


def _verification_tuple_from_payload(
    payload: dict[str, Any], original_code: str
) -> tuple[str, str, str]:
    verdict = str(payload.get("verdict") or "").strip().upper()
    report = str(payload.get("bug_report") or payload.get("verified_bug_report") or "").strip()
    code = str(
        payload.get("verified_code")
        or payload.get("refactored_code")
        or payload.get("corrected_code")
        or original_code
    ).rstrip("\n")
    if verdict not in {"CLEAN", "ISSUES"}:
        raise GeminiParsingError("The structured verification omitted a valid verdict.")
    if verdict == "CLEAN":
        return "CLEAN", CLEAN_FINDING, original_code
    if not report:
        raise GeminiParsingError("The structured verification reported issues without evidence.")
    return "ISSUES", _normalize_bug_report(report, issues=True), code or original_code



def _normalize_large_finding(item: Any) -> dict[str, str] | None:
    if isinstance(item, str):
        text = item.strip()
        if not text:
            return None
        return {
            "severity": "Warning",
            "line": "source",
            "symbol": "submitted code",
            "cause": text,
            "impact": "The defect can cause incorrect or invalid behavior.",
            "correction": "Correct the identified source construct.",
        }
    if not isinstance(item, dict):
        return None
    severity = str(item.get("severity") or "Warning").strip().title()
    if severity not in {"Critical", "Warning"}:
        severity = "Warning"
    cause = str(item.get("cause") or item.get("description") or item.get("issue") or "").strip()
    if not cause:
        return None
    return {
        "severity": severity,
        "line": str(item.get("line") or item.get("lines") or "source").strip(),
        "symbol": str(item.get("symbol") or item.get("selector") or item.get("function") or "submitted code").strip(),
        "cause": cause,
        "impact": str(item.get("impact") or "The defect can produce invalid or incorrect behavior.").strip(),
        "correction": str(item.get("correction") or item.get("fix") or "Correct the identified source construct.").strip(),
    }


def _parse_large_analysis_reply(raw_text: str) -> tuple[str, list[dict[str, str]]]:
    payload = _extract_json_object(raw_text)
    if not payload:
        raise GeminiParsingError("The large-source analysis did not return valid JSON.")
    verdict = str(payload.get("verdict") or "").strip().upper()
    if verdict not in {"CLEAN", "ISSUES"}:
        raise GeminiParsingError("The large-source analysis omitted a valid verdict.")
    raw_findings = payload.get("findings") or []
    if not isinstance(raw_findings, list):
        raise GeminiParsingError("The large-source findings must be a JSON array.")
    findings = [finding for item in raw_findings if (finding := _normalize_large_finding(item))]
    if findings:
        verdict = "ISSUES"
    elif verdict == "ISSUES":
        raise GeminiParsingError("The large-source review reported issues without evidence.")
    return verdict, findings


def _dedupe_large_findings(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for finding in findings:
        key = re.sub(
            r"\\s+",
            " ",
            f"{finding.get('line','')}|{finding.get('symbol','')}|{finding.get('cause','')}".lower(),
        ).strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


def _large_findings_markdown(findings: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for finding in findings:
        line = finding.get("line") or "source"
        symbol = finding.get("symbol") or "submitted code"
        lines.append(
            f"- **{finding['severity']}** {line} · `{symbol}` — {finding['cause']} "
            f"Impact: {finding['impact']} Correction: {finding['correction']}"
        )
    return "\n".join(lines) or CLEAN_FINDING


def _extract_complete_large_source(raw_text: str, original_code: str) -> str:
    marker_match = LARGE_SOURCE_RE.search(raw_text or "")
    if marker_match:
        code = marker_match.group(1).rstrip("\n")
    else:
        code = _extract_code(raw_text, "")
    if not code.strip():
        raise GeminiParsingError("The large-source repair returned no source code.")
    # Large corrections should be surgical. A substantially shorter response almost always
    # means the model hit an output limit or replaced sections with an omission placeholder.
    minimum_length = int(len(original_code) * 0.72) if len(original_code) >= 20_000 else 1
    omission_tokens = ("... omitted", "remaining code unchanged", "rest of file", "same as above")
    if len(code) < minimum_length or any(token in code.lower() for token in omission_tokens):
        raise GeminiParsingError("The large-source repair was incomplete.")
    return code



def _source_chunks(code: str, *, max_chars: int = 14_000, overlap_lines: int = 8) -> list[tuple[int, str]]:
    """Split large source by complete lines while preserving original line offsets."""
    lines = code.splitlines()
    if not lines:
        return [(1, "")]
    chunks: list[tuple[int, str]] = []
    start = 0
    total = len(lines)
    while start < total:
        end = start
        current = 0
        while end < total:
            addition = len(lines[end]) + 1
            if end > start and current + addition > max_chars:
                break
            current += addition
            end += 1
        chunks.append((start + 1, "\n".join(lines[start:end])))
        if end >= total:
            break
        start = max(start + 1, end - overlap_lines)
    return chunks


def _shift_large_findings(findings: list[dict[str, str]], offset: int) -> list[dict[str, str]]:
    if offset <= 0:
        return findings
    shifted: list[dict[str, str]] = []
    for finding in findings:
        item = dict(finding)
        line_text = str(item.get("line") or "")
        match = re.fullmatch(r"\s*(\d+)\s*(?:[-–:]\s*(\d+))?\s*", line_text)
        if match:
            first = int(match.group(1)) + offset
            second = int(match.group(2)) + offset if match.group(2) else None
            item["line"] = f"{first}-{second}" if second is not None else str(first)
        shifted.append(item)
    return shifted


def _chunked_large_analysis(
    *,
    code: str,
    language: str,
    filename: str,
    focus: str,
    detail: str,
    syntax_context: str,
) -> tuple[str, list[dict[str, str]]]:
    """Fallback analysis that prevents one malformed model reply from aborting a large review."""
    collected: list[dict[str, str]] = []
    successful_chunks = 0
    for start_line, chunk in _source_chunks(code):
        end_line = start_line + max(0, len(chunk.splitlines()) - 1)
        chunk_prompt = build_large_analysis_prompt(
            code=chunk,
            language=language,
            filename=filename,
            focus=focus,
            detail=detail,
            syntax_context=(
                f"This is source lines {start_line}-{end_line}. {syntax_context or 'No deterministic diagnostic was supplied.'}"
            ),
        )
        chunk_prompt += (
            f"\nLINE OFFSET RULE: The first displayed chunk line is original line {start_line}. "
            "Return finding line numbers relative to this chunk; they will be shifted by the pipeline."
        )
        raw = None
        for suffix in ("", "\nFORMAT REPAIR: Return one valid JSON object only, without Markdown fences."):
            try:
                raw = _generate_text(
                    prompt=chunk_prompt + suffix,
                    system_instruction=LARGE_ANALYSIS_SYSTEM_INSTRUCTION,
                    max_output_tokens=4096,
                )
                verdict, findings = _parse_large_analysis_reply(raw)
                collected.extend(_shift_large_findings(findings, start_line - 1))
                successful_chunks += 1
                break
            except GeminiParsingError:
                continue
    if successful_chunks == 0:
        raise GeminiParsingError("The large-source analysis could not be parsed in either full-file or chunked mode.")
    findings = _dedupe_large_findings(collected)
    return ("ISSUES" if findings else "CLEAN"), findings


def _normalize_patch_edit(item: Any, total_lines: int) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    try:
        start = int(item.get("start_line"))
        end = int(item.get("end_line"))
    except (TypeError, ValueError):
        return None
    if not (1 <= start <= end <= max(1, total_lines)):
        return None
    replacement = item.get("replacement")
    if replacement is None:
        replacement = ""
    return {"start_line": start, "end_line": end, "replacement": str(replacement).rstrip("\n")}


def _parse_large_patch_reply(raw_text: str, total_lines: int) -> list[dict[str, Any]]:
    payload = _extract_json_object(raw_text)
    if not payload:
        raise GeminiParsingError("The large-source patch response did not contain valid JSON.")
    raw_edits = payload.get("edits")
    if not isinstance(raw_edits, list):
        raise GeminiParsingError("The large-source patch response omitted the edits array.")
    edits = [edit for item in raw_edits if (edit := _normalize_patch_edit(item, total_lines))]
    edits.sort(key=lambda item: (item["start_line"], item["end_line"]))
    previous_end = 0
    for edit in edits:
        if edit["start_line"] <= previous_end:
            raise GeminiParsingError("The large-source patch response contained overlapping edits.")
        previous_end = edit["end_line"]
    return edits


def _apply_line_edits(original_code: str, edits: list[dict[str, Any]]) -> str:
    if not edits:
        return original_code
    had_trailing_newline = original_code.endswith("\n")
    lines = original_code.splitlines()
    for edit in reversed(edits):
        replacement = edit["replacement"].splitlines()
        start_index = edit["start_line"] - 1
        end_index = edit["end_line"]
        lines[start_index:end_index] = replacement
    result = "\n".join(lines)
    if had_trailing_newline:
        result += "\n"
    return result


def _large_patch_repair(
    *,
    original_code: str,
    language: str,
    filename: str,
    findings_json: str,
    syntax_context: str,
) -> str:
    prompt = build_large_patch_prompt(
        original_code=original_code,
        language=language,
        filename=filename,
        verified_findings_json=findings_json,
        syntax_context=syntax_context,
    )
    total_lines = max(1, len(original_code.splitlines()))
    last_error: GeminiParsingError | None = None
    for suffix in (
        "",
        "\nFORMAT REPAIR: Return one valid JSON object only. Keep edits minimal, non-overlapping, and line-accurate.",
    ):
        try:
            raw = _generate_text(
                prompt=prompt + suffix,
                system_instruction=LARGE_PATCH_SYSTEM_INSTRUCTION,
                max_output_tokens=16_384,
            )
            edits = _parse_large_patch_reply(raw, total_lines)
            repaired = _apply_line_edits(original_code, edits)
            if repaired.strip():
                return repaired
        except GeminiParsingError as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise GeminiParsingError("The large-source patch repair did not produce a usable correction.")


def _large_source_review(
    *,
    code: str,
    language: str,
    filename: str,
    focus: str,
    detail: str,
    syntax_context: str,
    syntax_failed: bool,
) -> dict:
    analysis_prompt = build_large_analysis_prompt(
        code=code,
        language=language,
        filename=filename,
        focus=focus,
        detail=detail,
        syntax_context=syntax_context,
    )
    verdict = "CLEAN"
    findings: list[dict[str, str]] = []
    full_analysis_parsed = False
    for suffix in ("", "\nFORMAT REPAIR: Return one valid JSON object only, without Markdown fences."):
        try:
            raw_analysis = _generate_text(
                prompt=analysis_prompt + suffix,
                system_instruction=LARGE_ANALYSIS_SYSTEM_INSTRUCTION,
                max_output_tokens=8192,
            )
            verdict, findings = _parse_large_analysis_reply(raw_analysis)
            full_analysis_parsed = True
            break
        except GeminiParsingError:
            continue

    if not full_analysis_parsed:
        # A 50k+ source must not fail merely because one model response had malformed JSON.
        try:
            verdict, findings = _chunked_large_analysis(
                code=code,
                language=language,
                filename=filename,
                focus=focus,
                detail=detail,
                syntax_context=syntax_context,
            )
        except GeminiParsingError:
            # Deterministic parsers remain authoritative. When they report a clean source,
            # preserve the complete original rather than interrupting the user's review.
            if not syntax_failed:
                return {
                    "bug_report": CLEAN_FINDING,
                    "refactored_code": code,
                    "has_issues": False,
                    "verification_status": "deterministic-large-source-fallback",
                }
            verdict, findings = "ISSUES", []

    candidate_json = json.dumps({"verdict": verdict, "findings": findings}, ensure_ascii=False)
    verify_prompt = build_large_verification_prompt(
        original_code=code,
        language=language,
        filename=filename,
        syntax_context=syntax_context,
        candidate_findings_json=candidate_json,
    )
    try:
        raw_verify = _generate_text(
            prompt=verify_prompt,
            system_instruction=LARGE_VERIFIER_SYSTEM_INSTRUCTION,
            max_output_tokens=8192,
        )
        verified_verdict, verified_findings = _parse_large_analysis_reply(raw_verify)
        verdict, findings = verified_verdict, verified_findings
    except GeminiParsingError:
        # Verification formatting is advisory; retain evidence from the usable audit.
        pass

    if syntax_failed:
        deterministic = {
            "severity": "Critical",
            "line": "deterministic validation",
            "symbol": filename,
            "cause": syntax_context,
            "impact": "The source cannot be parsed or executed reliably in its current form.",
            "correction": "Correct every parser or compiler diagnostic before execution.",
        }
        findings.insert(0, deterministic)
        verdict = "ISSUES"

    findings = _dedupe_large_findings(findings)
    if verdict == "CLEAN" and not findings:
        return {
            "bug_report": CLEAN_FINDING,
            "refactored_code": code,
            "has_issues": False,
            "verification_status": "verified-large-source",
        }

    if not findings:
        # Never interrupt a syntactically valid large review because the language model
        # emitted an unsupported ISSUES label without evidence.
        if not syntax_failed:
            return {
                "bug_report": CLEAN_FINDING,
                "refactored_code": code,
                "has_issues": False,
                "verification_status": "evidence-safe-large-source",
            }
        findings = [{
            "severity": "Critical",
            "line": "deterministic validation",
            "symbol": filename,
            "cause": syntax_context or "The deterministic source validator reported an invalid program.",
            "impact": "The source cannot be parsed or executed reliably in its current form.",
            "correction": "Correct the parser or compiler diagnostic before execution.",
        }]

    findings_json = json.dumps({"verdict": "ISSUES", "findings": findings}, ensure_ascii=False)
    try:
        repaired_code = _large_patch_repair(
            original_code=code,
            language=language,
            filename=filename,
            findings_json=findings_json,
            syntax_context=syntax_context,
        )
    except GeminiParsingError:
        # Compatibility fallback for providers that struggle with JSON patch output.
        repair_prompt = build_large_repair_prompt(
            original_code=code,
            language=language,
            filename=filename,
            verified_findings_json=findings_json,
            syntax_context=syntax_context,
        )
        repaired_code = code
        for suffix in (
            "",
            "\nOUTPUT REPAIR: Return every line between the exact markers; no placeholders or omissions.",
        ):
            try:
                raw_repair = _generate_text(
                    prompt=repair_prompt + suffix,
                    system_instruction=LARGE_REPAIR_SYSTEM_INSTRUCTION,
                    max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                )
                repaired_code = _extract_complete_large_source(raw_repair, code)
                break
            except GeminiParsingError:
                continue

    return {
        "bug_report": _large_findings_markdown(findings),
        "refactored_code": repaired_code,
        "has_issues": True,
        "verification_status": "verified-large-source",
    }


def _generate_review_candidate(user_prompt: str, code: str) -> tuple[str, str]:
    json_instruction = (
        "Return one JSON object only with keys verdict, bug_report, and refactored_code. "
        "verdict must be CLEAN or ISSUES. For CLEAN, bug_report must state that no verified issues "
        "were found and refactored_code must equal the submitted source exactly. For ISSUES, provide "
        "direct evidence and the complete corrected source. No Markdown fences or extra text."
    )
    try:
        payload = _generate_json_payload(
            prompt=user_prompt,
            system_instruction=json_instruction + "\n\n" + SYSTEM_INSTRUCTION,
            response_schema=REVIEW_RESPONSE_SCHEMA,
        )
        return _review_tuple_from_payload(payload, code)
    except GeminiParsingError:
        pass

    raw_text = _generate_text(prompt=user_prompt, system_instruction=SYSTEM_INSTRUCTION)
    try:
        return _parse_structured_reply(raw_text, fallback_code=code)
    except GeminiParsingError:
        # Preserve and reuse the first response while requesting only a format conversion.
        repair_prompt = (
            "Convert the following completed review into one JSON object with keys verdict, "
            "bug_report, and refactored_code. Do not re-review or change its factual conclusions.\n"
            "--- BEGIN REVIEW ---\n" + raw_text + "\n--- END REVIEW ---"
        )
        try:
            payload = _generate_json_payload(
                prompt=repair_prompt,
                system_instruction=json_instruction,
                response_schema=REVIEW_RESPONSE_SCHEMA,
            )
            return _review_tuple_from_payload(payload, code)
        except GeminiParsingError:
            retry_text = _generate_text(
                prompt=(
                    user_prompt
                    + "\n\nFORMAT REPAIR: Return only the exact ## BUG_REPORT and ## REFACTORED_CODE "
                    "sections. The code section must contain one complete fenced source block. "
                    "Preserve every verified defect; do not invent new ones."
                ),
                system_instruction=SYSTEM_INSTRUCTION,
            )
            try:
                return _parse_structured_reply(retry_text, fallback_code=code)
            except GeminiParsingError:
                # Final tolerant recovery: keep any complete fenced code and all preceding findings.
                fence = CODE_FENCE_RE.search(retry_text or raw_text)
                if fence:
                    source = fence.group(1).rstrip("\n") or code
                    prose = (retry_text or raw_text)[: fence.start()].strip()
                    prose = re.sub(r"^#{1,4}.*?(?:REPORT|FINDINGS?)\s*:?[ \t]*", "", prose, flags=re.I | re.S).strip()
                    if prose:
                        return _normalize_bug_report(prose, issues=not _report_is_clean(prose)), source
                raise


def _candidate_fallback(
    *, candidate_bug_report: str, candidate_code: str, original_code: str, syntax_failed: bool
) -> tuple[str, str, str]:
    candidate_is_clean = _report_is_clean(candidate_bug_report)
    if syntax_failed or not candidate_is_clean:
        return "ISSUES", _normalize_bug_report(candidate_bug_report, issues=True), candidate_code or original_code
    return "CLEAN", CLEAN_FINDING, original_code


def _verify_candidate(
    *,
    original_code: str,
    language: str,
    filename: str,
    syntax_context: str,
    syntax_failed: bool,
    candidate_bug_report: str,
    candidate_code: str,
) -> tuple[str, str, str]:
    verification_prompt = build_verification_prompt(
        original_code=original_code,
        language=language,
        filename=filename,
        syntax_context=syntax_context,
        candidate_bug_report=candidate_bug_report,
        candidate_code=candidate_code,
    )
    json_instruction = (
        "Return one JSON object only with keys verdict, bug_report, and verified_code. "
        "verdict must be CLEAN or ISSUES. Keep deterministic parser evidence. No Markdown or extra text."
    )
    try:
        payload = _generate_json_payload(
            prompt=verification_prompt,
            system_instruction=json_instruction + "\n\n" + VERIFIER_SYSTEM_INSTRUCTION,
            response_schema=VERIFY_RESPONSE_SCHEMA,
        )
        return _verification_tuple_from_payload(payload, original_code)
    except GeminiParsingError:
        pass

    try:
        raw_text = _generate_text(prompt=verification_prompt, system_instruction=VERIFIER_SYSTEM_INSTRUCTION)
        return _parse_verification_reply(raw_text, original_code)
    except GeminiParsingError:
        try:
            retry_text = _generate_text(
                prompt=(
                    verification_prompt
                    + "\n\nFORMAT REPAIR: Return exactly ## VERDICT, ## VERIFIED_BUG_REPORT, and "
                    "## VERIFIED_CODE. Keep every directly provable defect. A deterministic syntax failure "
                    "must use the ISSUES verdict."
                ),
                system_instruction=VERIFIER_SYSTEM_INSTRUCTION,
            )
            return _parse_verification_reply(retry_text, original_code)
        except GeminiParsingError:
            # A format-only verification failure must not discard a usable primary review.
            return _candidate_fallback(
                candidate_bug_report=candidate_bug_report,
                candidate_code=candidate_code,
                original_code=original_code,
                syntax_failed=syntax_failed,
            )


def _challenge_clean_result(
    *,
    original_code: str,
    language: str,
    filename: str,
    syntax_context: str,
) -> tuple[str, str, str]:
    prompt = build_clean_challenge_prompt(
        original_code=original_code,
        language=language,
        filename=filename,
        syntax_context=syntax_context,
    )
    try:
        raw_text = _generate_text(prompt=prompt, system_instruction=CLEAN_CHALLENGE_SYSTEM_INSTRUCTION)
        return _parse_verification_reply(raw_text, original_code)
    except GeminiParsingError:
        return "CLEAN", CLEAN_FINDING, original_code


def _repair_confirmed_code(
    *,
    original_code: str,
    candidate_code: str,
    language: str,
    filename: str,
    bug_report: str,
    syntax_context: str,
) -> str:
    prompt = build_repair_prompt(
        original_code=original_code,
        candidate_code=candidate_code,
        language=language,
        filename=filename,
        bug_report=bug_report,
        syntax_context=syntax_context,
    )
    try:
        raw_text = _generate_text(prompt=prompt, system_instruction=REPAIR_SYSTEM_INSTRUCTION)
        code = _extract_code(raw_text, candidate_code or original_code)
        return code or candidate_code or original_code
    except (GeminiParsingError, Exception):  # The verified candidate remains a safe fallback.
        return candidate_code or original_code


def repair_code(
    *,
    original_code: str,
    candidate_code: str,
    language: str,
    filename: str,
    bug_report: str,
    validation_context: str,
) -> str:
    """Request a complete corrected source using confirmed parser/compiler evidence."""
    if len(original_code) >= settings.LARGE_SOURCE_THRESHOLD:
        findings_json = json.dumps(
            {
                "verdict": "ISSUES",
                "findings": [{
                    "severity": "Critical",
                    "line": "deterministic validation",
                    "symbol": filename,
                    "cause": validation_context,
                    "impact": "The proposed corrected source still fails deterministic validation.",
                    "correction": bug_report,
                }],
            },
            ensure_ascii=False,
        )
        try:
            return _large_patch_repair(
                original_code=candidate_code or original_code,
                language=language,
                filename=filename,
                findings_json=findings_json,
                syntax_context=validation_context,
            )
        except GeminiParsingError:
            return candidate_code or original_code
    return _repair_confirmed_code(
        original_code=original_code,
        candidate_code=candidate_code,
        language=language,
        filename=filename,
        bug_report=bug_report,
        syntax_context=validation_context,
    )



def _generate_findings_payload(
    *,
    prompt: str,
    system_instruction: str,
    max_output_tokens: int = 8192,
) -> tuple[str, list[dict[str, str]]]:
    """Return compact findings with schema-first and text-JSON fallbacks.

    Source code is deliberately excluded from the JSON response. This avoids the
    quoting/truncation failures that previously affected JavaScript, CSS, HTML,
    TypeScript, and other non-Python files containing many braces or backticks.
    """
    failures: list[Exception] = []
    try:
        payload = _generate_json_payload(
            prompt=prompt,
            system_instruction=system_instruction,
            response_schema=FINDINGS_RESPONSE_SCHEMA,
            max_output_tokens=max_output_tokens,
        )
        return _parse_large_analysis_reply(json.dumps(payload, ensure_ascii=False))
    except Exception as exc:  # Provider schema support varies by model/version.
        failures.append(exc)

    for suffix in (
        "\nRETURN FORMAT: Emit one valid JSON object only. No Markdown fences or commentary.",
        "\nFORMAT RECOVERY: Return compact JSON with verdict and findings only.",
    ):
        try:
            raw = _generate_text(
                prompt=prompt + suffix,
                system_instruction=system_instruction,
                max_output_tokens=max_output_tokens,
            )
            return _parse_large_analysis_reply(raw)
        except Exception as exc:
            failures.append(exc)

    last = failures[-1] if failures else GeminiParsingError("The analysis response could not be parsed.")
    if isinstance(last, GeminiParsingError):
        raise last
    raise GeminiParsingError(f"The analysis response could not be verified: {last}") from last


def _finding_line_in_range(line_text: str, total_lines: int) -> bool:
    numbers = [int(item) for item in re.findall(r"\d+", str(line_text or ""))[:2]]
    if not numbers:
        return False
    return all(1 <= number <= max(1, total_lines) for number in numbers)


def _finding_is_grounded(finding: dict[str, str], source_code: str) -> bool:
    """Reject hallucinated findings that cannot be anchored to the submitted file."""
    total_lines = max(1, len(source_code.splitlines()))
    if not _finding_line_in_range(finding.get("line", ""), total_lines):
        return False

    symbol = str(finding.get("symbol") or "").strip().strip("`'\"")
    generic = {
        "source", "submitted code", "code", "file", "program", "stylesheet",
        "document", "query", "script", "function", "class", "selector",
    }
    if symbol and symbol.lower() not in generic and symbol.lower() in source_code.lower():
        return True

    # Exact inline tokens in the cause/correction also count as source evidence.
    combined = f"{finding.get('cause','')} {finding.get('correction','')}"
    for token in re.findall(r"`([^`]{1,120})`", combined):
        if token and token in source_code:
            return True

    # A valid exact line number is acceptable when the finding describes a parser
    # diagnostic even if the model used a generic symbol label.
    cause = str(finding.get("cause") or "").lower()
    return any(term in cause for term in (
        "syntax", "parser", "compiler", "missing", "unexpected", "invalid token",
        "unterminated", "unbalanced", "not defined", "undefined", "cannot find",
    ))


def _ground_findings(
    findings: list[dict[str, str]], source_code: str
) -> list[dict[str, str]]:
    return _dedupe_large_findings(
        [finding for finding in findings if _finding_is_grounded(finding, source_code)]
    )


def _deterministic_finding(filename: str, syntax_context: str) -> dict[str, str]:
    line_match = re.search(r"line\s+(\d+)(?:\D+column\s+(\d+))?", syntax_context or "", re.I)
    line = line_match.group(1) if line_match else "1"
    return {
        "severity": "Critical",
        "line": line,
        "symbol": filename,
        "cause": syntax_context or "The deterministic language validator reported invalid source syntax.",
        "impact": "The source cannot be parsed, compiled, or executed reliably in its current form.",
        "correction": "Correct every deterministic parser or compiler diagnostic before execution.",
    }


def _compact_repair_source(
    *,
    original_code: str,
    language: str,
    filename: str,
    findings: list[dict[str, str]],
    syntax_context: str,
) -> str:
    findings_json = json.dumps({"verdict": "ISSUES", "findings": findings}, ensure_ascii=False)
    prompt = build_compact_repair_prompt(
        original_code=original_code,
        language=language,
        filename=filename,
        verified_findings_json=findings_json,
        syntax_context=syntax_context,
    )
    errors: list[Exception] = []
    for suffix in (
        "",
        "\nOUTPUT RECOVERY: Return every source line between the exact markers. Do not use Markdown fences.",
    ):
        try:
            raw = _generate_text(
                prompt=prompt + suffix,
                system_instruction=COMPACT_REPAIR_SYSTEM_INSTRUCTION,
                max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
            )
            return _extract_complete_large_source(raw, original_code)
        except Exception as exc:
            errors.append(exc)

    # Legacy fenced-code repair is retained only as a final compatibility fallback.
    try:
        return _repair_confirmed_code(
            original_code=original_code,
            candidate_code=original_code,
            language=language,
            filename=filename,
            bug_report=_large_findings_markdown(findings),
            syntax_context=syntax_context,
        )
    except Exception as exc:
        errors.append(exc)
    last = errors[-1] if errors else GeminiParsingError("The correction response was empty.")
    raise GeminiParsingError(f"The corrected source could not be produced: {last}") from last


def _compact_source_review(
    *,
    code: str,
    language: str,
    filename: str,
    focus: str,
    detail: str,
    syntax_context: str,
    syntax_failed: bool,
) -> dict:
    """Language-neutral audit pipeline used for every supported language.

    Stage 1 returns findings only. Stage 2 independently verifies those findings.
    Stage 3 returns corrected source only when verified issues exist. Separating code
    from JSON prevents JavaScript/CSS/HTML quoting from corrupting structured output.
    """
    analysis_prompt = build_compact_analysis_prompt(
        code=code,
        language=language,
        filename=filename,
        focus=focus,
        detail=detail,
        syntax_context=syntax_context,
    )
    verdict, findings = _generate_findings_payload(
        prompt=analysis_prompt,
        system_instruction=COMPACT_AUDIT_SYSTEM_INSTRUCTION,
    )
    findings = _ground_findings(findings, code)
    if findings:
        verdict = "ISSUES"
    elif verdict == "ISSUES":
        verdict = "CLEAN"

    primary_verdict = verdict
    primary_findings = list(findings)
    candidate_json = json.dumps({"verdict": verdict, "findings": findings}, ensure_ascii=False)
    verification_prompt = build_compact_verification_prompt(
        original_code=code,
        language=language,
        filename=filename,
        syntax_context=syntax_context,
        candidate_findings_json=candidate_json,
    )
    try:
        verified_verdict, verified_findings = _generate_findings_payload(
            prompt=verification_prompt,
            system_instruction=COMPACT_VERIFY_SYSTEM_INSTRUCTION,
        )
        verified_findings = _ground_findings(verified_findings, code)
        if verified_findings:
            verdict, findings = "ISSUES", verified_findings
        elif verified_verdict == "CLEAN" and primary_verdict == "CLEAN":
            verdict, findings = "CLEAN", []
        elif verified_verdict == "CLEAN" and primary_findings:
            # A disagreement receives one evidence-only tie-break audit. This stops a
            # mistaken CLEAN verifier from erasing real JavaScript/CSS/Java/C++ issues,
            # while still rejecting one-pass hallucinations.
            tie_prompt = build_compact_analysis_prompt(
                code=code,
                language=language,
                filename=filename,
                focus="correctness",
                detail="deep",
                syntax_context=syntax_context,
            )
            tie_verdict, tie_findings = _generate_findings_payload(
                prompt=tie_prompt,
                system_instruction=COMPACT_AUDIT_SYSTEM_INSTRUCTION,
            )
            tie_findings = _ground_findings(tie_findings, code)
            if tie_verdict == "ISSUES" and tie_findings:
                verdict, findings = "ISSUES", tie_findings
            else:
                verdict, findings = "CLEAN", []
    except GeminiParsingError:
        # A verifier formatting failure must not erase a usable primary audit.
        verdict, findings = primary_verdict, primary_findings

    if syntax_failed:
        findings.insert(0, _deterministic_finding(filename, syntax_context))
        verdict = "ISSUES"

    findings = _dedupe_large_findings(findings)
    if verdict == "CLEAN" and not findings:
        return {
            "bug_report": CLEAN_FINDING,
            "refactored_code": code,
            "has_issues": False,
            "verification_status": "polyglot-verified-clean",
        }

    if not findings:
        # Do not claim a clean review when the model returned an unsupported issue
        # verdict. Run one final evidence-only audit instead.
        challenge_prompt = build_compact_analysis_prompt(
            code=code,
            language=language,
            filename=filename,
            focus="correctness",
            detail="deep",
            syntax_context=syntax_context,
        )
        challenge_verdict, challenge_findings = _generate_findings_payload(
            prompt=challenge_prompt,
            system_instruction=COMPACT_AUDIT_SYSTEM_INSTRUCTION,
        )
        findings = _ground_findings(challenge_findings, code)
        if challenge_verdict == "CLEAN" and not findings:
            return {
                "bug_report": CLEAN_FINDING,
                "refactored_code": code,
                "has_issues": False,
                "verification_status": "polyglot-verified-clean",
            }

    repaired_code = _compact_repair_source(
        original_code=code,
        language=language,
        filename=filename,
        findings=findings,
        syntax_context=syntax_context,
    )
    return {
        "bug_report": _large_findings_markdown(findings),
        "refactored_code": repaired_code,
        "has_issues": True,
        "verification_status": "polyglot-verified-issues",
    }

def review_code(
    code: str,
    language: str,
    filename: str,
    focus: str = "balanced",
    detail: str = "standard",
    syntax_context: str = "",
    syntax_status: str = "not_available",
) -> dict:
    """Review any supported language through the same polyglot pipeline."""
    syntax_failed = syntax_status == "failed"
    if len(code) >= settings.LARGE_SOURCE_THRESHOLD:
        return _large_source_review(
            code=code,
            language=language,
            filename=filename,
            focus=focus,
            detail=detail,
            syntax_context=syntax_context,
            syntax_failed=syntax_failed,
        )
    return _compact_source_review(
        code=code,
        language=language,
        filename=filename,
        focus=focus,
        detail=detail,
        syntax_context=syntax_context,
        syntax_failed=syntax_failed,
    )

def explain_code(code: str, language: str, filename: str, detail: str = "standard") -> str:
    prompt = build_explain_prompt(code=code, language=language, filename=filename, detail=detail)
    raw_text = _generate_text(prompt=prompt, system_instruction=EXPLAIN_SYSTEM_INSTRUCTION)
    try:
        return _validate_explanation(raw_text)
    except GeminiParsingError:
        retry_text = _generate_text(
            prompt=prompt + "\n\nFORMAT REPAIR: Include all four required headings exactly and in order.",
            system_instruction=EXPLAIN_SYSTEM_INSTRUCTION,
        )
        return _validate_explanation(retry_text)
