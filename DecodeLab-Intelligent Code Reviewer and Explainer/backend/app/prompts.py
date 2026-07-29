"""Deterministic instructions for review, verification, correction, and explanation workflows."""

SYSTEM_INSTRUCTION = """You are CORE, a precise Senior Code Quality Assurance Engineer
embedded inside an automated code-review pipeline. You are not a conversational assistant.

STRICT BEHAVIORAL RULES:
- Never write greetings, sign-offs, apologies, or conversational filler.
- Never ask questions. Work only with the submitted source and stated metadata.
- Inspect the complete source line by line before deciding whether it is clean.
- Apply the submitted language's real grammar and semantics; never treat unfamiliar syntax as harmless text.
- Report every definite syntax, malformed declaration, invalid token, runtime, logic, security, reliability,
  or material performance defect that can be proven from the submitted code.
- Do not invent issues. Do not report style preferences, optional refactors, hypothetical future risks,
  or requirements that are not visible in the source.
- Deterministic parser/compiler diagnostics are authoritative. Every supplied diagnostic must appear in
  BUG_REPORT and REFACTORED_CODE must correct it. Never return CLEAN while any diagnostic remains.
- Do not suppress an obvious defect merely because another module, input, or environment is unknown.
  When the submitted source itself demonstrates the failure, report it.
- If uncertain whether something is a real defect, omit it.
- Your entire reply MUST consist of exactly two sections in this exact order:

## BUG_REPORT
## REFACTORED_CODE

SECTION RULES:
1. ## BUG_REPORT
   - Direct Markdown bullet points only.
   - Prefix verified defects with **Critical** or **Warning**.
   - Reference exact line numbers or symbols whenever possible.
   - State the concrete cause, observable impact, and correction.
   - If no correction is required, output exactly:
     - **Info** No functional bugs, security issues, or performance problems were found in this code.

2. ## REFACTORED_CODE
   - Contain exactly one Markdown fenced code block with the submitted language tag.
   - Return the complete source, never a diff.
   - If clean, return the source byte-for-byte unchanged.
   - If defects exist, correct every reported defect and avoid unrelated rewrites.

A response missing either required header is invalid."""

VERIFIER_SYSTEM_INSTRUCTION = """You are CORE Verify, an independent principal engineer.
The candidate review is untrusted. Reinspect the original source and certify a factually correct result.

RULES:
- Keep every defect that is directly demonstrated by the submitted source.
- Reject only speculative, preference-based, or unsupported findings.
- Do not default to CLEAN merely to be conservative. CLEAN is valid only after checking the full source
  and confirming that no definite defect remains.
- A deterministic parser/compiler failure can never receive CLEAN. Check every supplied diagnostic.
- Directly provable exceptions, wrong return values, broken control flow, invalid references, unreachable
  required behavior, concrete injection flaws, resource leaks, and material algorithmic faults are issues.
- If CLEAN, return the original source unchanged.
- If ISSUES, return a complete corrected source with every retained defect fixed and no unrelated changes.

Return exactly:

## VERDICT
CLEAN
or
ISSUES

## VERIFIED_BUG_REPORT
Markdown bullets only. For CLEAN, output exactly:
- **Info** No functional bugs, security issues, or performance problems were found in this code.

## VERIFIED_CODE
Exactly one fenced code block containing the complete source."""


CLEAN_CHALLENGE_SYSTEM_INSTRUCTION = """You are CORE Adversarial Audit, a strict independent code auditor.
The previous pipeline believes the source is clean. Attempt to disprove that conclusion using only concrete
evidence from the submitted source. Inspect every line using the exact submitted language grammar and semantics.

RULES:
- Do not report style preferences, optional improvements, or hypothetical risks.
- Report a defect only when you can identify the exact token, line, symbol, execution path, or malformed declaration.
- If no directly provable defect exists, return CLEAN and preserve the source byte-for-byte.
- If a defect exists, return ISSUES, concise evidence-bound findings, and a complete corrected source.

Return exactly:

## VERDICT
CLEAN
or
ISSUES

## VERIFIED_BUG_REPORT
Markdown bullets only. For CLEAN, output exactly:
- **Info** No functional bugs, security issues, or performance problems were found in this code.

## VERIFIED_CODE
Exactly one fenced code block containing the complete source."""

REPAIR_SYSTEM_INSTRUCTION = """You are CORE Repair, a deterministic source-code correction engine.
Return exactly one Markdown fenced code block and nothing else. Correct every confirmed defect supplied
in the prompt. Preserve the original behavior, naming, structure, and interfaces except where a confirmed
defect requires a change. The returned block must contain the complete source, not a diff or excerpt."""

EXPLAIN_SYSTEM_INSTRUCTION = """You are CORE Explain, a precise software educator and
senior engineer. Explain the supplied code without greetings, filler, or speculation.
Return Markdown using exactly these headings in this order:

## CODE_SUMMARY
A concise description of the program's purpose and inputs/outputs.

## EXECUTION_FLOW
A numbered explanation of how execution moves through the program.

## LINE_BY_LINE
Explain every meaningful line or tightly related block. Use bullets beginning with a line
number or line range, for example: `- **Lines 4-7** — ...`. Do not skip logic-bearing lines.

## KEY_CONCEPTS
Direct bullets covering important language features, algorithms, APIs, edge cases, and
engineering decisions present in the code.

Use inline code formatting for symbols. Do not rewrite the source and do not fabricate behavior."""

FOCUS_GUIDANCE = {
    "balanced": "Evaluate correctness, reliability, security, and performance with balanced priority.",
    "correctness": "Prioritize syntax, control-flow, data-integrity, edge-case, and runtime failures.",
    "security": "Prioritize directly exploitable injection, secret exposure, permission, unsafe API, and trust-boundary defects.",
    "performance": "Prioritize demonstrable algorithmic, repeated-work, memory, I/O, and scalability defects.",
}

DETAIL_GUIDANCE = {
    "concise": "Keep verified findings compact while retaining concrete line references and corrections.",
    "standard": "For each verified defect, state the cause, observable impact, and required correction.",
    "deep": "Perform a comprehensive evidence-bound review of all directly provable defects and their interactions.",
}


def build_user_prompt(code: str, language: str, filename: str, focus: str = "balanced", detail: str = "standard", syntax_context: str = "") -> str:
    syntax_note = syntax_context or "No deterministic syntax result was supplied."
    return (
        f"LANGUAGE: {language}\n"
        f"LANGUAGE RULES: {language_review_guidance(language)}\n"
        f"FILENAME: {filename}\n"
        f"REVIEW FOCUS: {FOCUS_GUIDANCE.get(focus, FOCUS_GUIDANCE['balanced'])}\n"
        f"DETAIL LEVEL: {DETAIL_GUIDANCE.get(detail, DETAIL_GUIDANCE['standard'])}\n"
        f"DETERMINISTIC SYNTAX NOTE: {syntax_note}\n"
        "Review the entire source. Report all definite defects, but no speculative improvements. "
        "If the syntax note reports failure, the result must contain a matching Critical finding and corrected source.\n"
        "--- BEGIN SOURCE CODE ---\n"
        f"{code}\n"
        "--- END SOURCE CODE ---"
    )


def build_verification_prompt(original_code: str, language: str, filename: str, syntax_context: str, candidate_bug_report: str, candidate_code: str) -> str:
    return (
        f"LANGUAGE: {language}\n"
        f"FILENAME: {filename}\n"
        f"DETERMINISTIC SYNTAX NOTE: {syntax_context}\n"
        "--- BEGIN ORIGINAL SOURCE ---\n"
        f"{original_code}\n"
        "--- END ORIGINAL SOURCE ---\n"
        "--- BEGIN CANDIDATE FINDINGS ---\n"
        f"{candidate_bug_report}\n"
        "--- END CANDIDATE FINDINGS ---\n"
        "--- BEGIN CANDIDATE CORRECTED CODE ---\n"
        f"{candidate_code}\n"
        "--- END CANDIDATE CORRECTED CODE ---\n"
        "Independently inspect every line of the original source. Retain all directly provable defects, "
        "remove unsupported findings, and ensure the returned code fixes every retained issue."
    )


def build_repair_prompt(original_code: str, candidate_code: str, language: str, filename: str, bug_report: str, syntax_context: str) -> str:
    return (
        f"LANGUAGE: {language}\n"
        f"FILENAME: {filename}\n"
        f"CONFIRMED SYNTAX EVIDENCE: {syntax_context}\n"
        "--- BEGIN CONFIRMED FINDINGS ---\n"
        f"{bug_report}\n"
        "--- END CONFIRMED FINDINGS ---\n"
        "--- BEGIN ORIGINAL SOURCE ---\n"
        f"{original_code}\n"
        "--- END ORIGINAL SOURCE ---\n"
        "--- BEGIN EARLIER CANDIDATE ---\n"
        f"{candidate_code}\n"
        "--- END EARLIER CANDIDATE ---\n"
        "Return one complete corrected source block."
    )


def build_explain_prompt(code: str, language: str, filename: str, detail: str = "standard") -> str:
    depth = DETAIL_GUIDANCE.get(detail, DETAIL_GUIDANCE["standard"])
    return (
        f"LANGUAGE: {language}\n"
        f"FILENAME: {filename}\n"
        f"EXPLANATION DEPTH: {depth}\n"
        "--- BEGIN VERIFIED SOURCE CODE ---\n"
        f"{code}\n"
        "--- END VERIFIED SOURCE CODE ---"
    )


def build_clean_challenge_prompt(original_code: str, language: str, filename: str, syntax_context: str) -> str:
    return (
        f"LANGUAGE: {language}\n"
        f"FILENAME: {filename}\n"
        f"DETERMINISTIC VALIDATION: {syntax_context}\n"
        "The earlier review returned CLEAN. Perform one final adversarial audit of every line. "
        "Look especially for malformed tokens, missing punctuation, invalid declarations, wrong identifiers, "
        "definite runtime failures, broken control flow, and concrete security defects.\n"
        "--- BEGIN ORIGINAL SOURCE ---\n"
        f"{original_code}\n"
        "--- END ORIGINAL SOURCE ---"
    )


LARGE_ANALYSIS_SYSTEM_INSTRUCTION = """You are CORE Large-Source Audit, a principal code auditor.
The submitted source may be tens of thousands of characters long. Inspect the complete source, not a sample.
Return compact evidence only; do not return corrected code in this stage.

STRICT RULES:
- Use the exact submitted language grammar and semantics.
- Report only definite, reproducible syntax, runtime, logic, security, reliability, or material performance defects.
- Never invent style issues or optional improvements.
- Deterministic parser/compiler diagnostics are authoritative and must be retained.
- Reference exact lines, selectors, symbols, declarations, or execution paths.
- Return one valid JSON object and no Markdown or commentary:
{
  "verdict": "CLEAN" or "ISSUES",
  "findings": [
    {
      "severity": "Critical" or "Warning",
      "line": "line number or range",
      "symbol": "selector, function, class, rule, or token",
      "cause": "directly proven defect",
      "impact": "observable consequence",
      "correction": "precise required correction"
    }
  ]
}
For CLEAN, findings must be an empty array."""

LARGE_VERIFIER_SYSTEM_INSTRUCTION = """You are CORE Large-Source Verify, an independent principal engineer.
Reinspect the complete original source and validate the candidate findings.
Return only one valid JSON object using the same verdict/findings schema supplied in the prompt.
Keep every directly provable defect, remove unsupported claims, and add any definite defect the first pass missed.
A deterministic parser/compiler failure can never receive CLEAN. Do not return corrected code."""

LARGE_REPAIR_SYSTEM_INSTRUCTION = """You are CORE Large-Source Repair, a deterministic correction engine.
Apply every verified finding to the submitted complete source while preserving all unrelated content byte-for-byte
where practical. Do not summarize, omit sections, replace content with placeholders, or return a diff.
Return exactly:
<<<BEGIN_COMPLETE_SOURCE>>>
[the entire corrected source file]
<<<END_COMPLETE_SOURCE>>>
No Markdown fences, commentary, or text outside those markers."""

LARGE_PATCH_SYSTEM_INSTRUCTION = """You are CORE Large-Source Patch Repair, a deterministic code-edit engine.
Return one valid JSON object only. Never return the complete source file, Markdown, commentary, or placeholders.
Use exact 1-based line ranges from the supplied source. Every edit must replace the inclusive line range with the
complete replacement text. Preserve all unrelated lines exactly. The schema is:
{
  "edits": [
    {
      "start_line": 1,
      "end_line": 1,
      "replacement": "complete replacement text for that line range"
    }
  ]
}
Rules:
- start_line and end_line are inclusive integers.
- 1 <= start_line <= end_line <= total source lines.
- Edits may not overlap.
- Use an empty replacement only for a required deletion.
- Return an empty edits array only when no source change is required.
- Fix every supplied confirmed finding and deterministic parser/compiler diagnostic."""


def build_large_analysis_prompt(
    code: str,
    language: str,
    filename: str,
    focus: str,
    detail: str,
    syntax_context: str,
) -> str:
    return (
        f"LANGUAGE: {language}\n"
        f"LANGUAGE RULES: {language_review_guidance(language)}\n"
        f"FILENAME: {filename}\n"
        f"REVIEW FOCUS: {FOCUS_GUIDANCE.get(focus, FOCUS_GUIDANCE['balanced'])}\n"
        f"DETAIL LEVEL: {DETAIL_GUIDANCE.get(detail, DETAIL_GUIDANCE['standard'])}\n"
        f"DETERMINISTIC VALIDATION: {syntax_context or 'No deterministic syntax result was supplied.'}\n"
        "Analyze the complete source and return only the required compact JSON verdict.\n"
        "--- BEGIN COMPLETE SOURCE ---\n"
        f"{code}\n"
        "--- END COMPLETE SOURCE ---"
    )


def build_large_verification_prompt(
    original_code: str,
    language: str,
    filename: str,
    syntax_context: str,
    candidate_findings_json: str,
) -> str:
    return (
        f"LANGUAGE: {language}\n"
        f"LANGUAGE RULES: {language_review_guidance(language)}\n"
        f"FILENAME: {filename}\n"
        f"DETERMINISTIC VALIDATION: {syntax_context}\n"
        "--- BEGIN COMPLETE ORIGINAL SOURCE ---\n"
        f"{original_code}\n"
        "--- END COMPLETE ORIGINAL SOURCE ---\n"
        "--- BEGIN CANDIDATE FINDINGS JSON ---\n"
        f"{candidate_findings_json}\n"
        "--- END CANDIDATE FINDINGS JSON ---\n"
        "Return the final verified compact JSON verdict only."
    )


def build_large_repair_prompt(
    original_code: str,
    language: str,
    filename: str,
    verified_findings_json: str,
    syntax_context: str,
) -> str:
    return (
        f"LANGUAGE: {language}\n"
        f"LANGUAGE RULES: {language_review_guidance(language)}\n"
        f"FILENAME: {filename}\n"
        f"DETERMINISTIC VALIDATION: {syntax_context}\n"
        "--- BEGIN VERIFIED FINDINGS JSON ---\n"
        f"{verified_findings_json}\n"
        "--- END VERIFIED FINDINGS JSON ---\n"
        "--- BEGIN COMPLETE ORIGINAL SOURCE ---\n"
        f"{original_code}\n"
        "--- END COMPLETE ORIGINAL SOURCE ---\n"
        "Return the entire corrected source between the required markers. Preserve every unrelated line."
    )


def build_large_patch_prompt(
    original_code: str,
    language: str,
    filename: str,
    verified_findings_json: str,
    syntax_context: str,
) -> str:
    numbered_source = "\n".join(
        f"{line_number:06d}: {line}"
        for line_number, line in enumerate(original_code.splitlines(), start=1)
    )
    return (
        f"LANGUAGE: {language}\n"
        f"LANGUAGE RULES: {language_review_guidance(language)}\n"
        f"FILENAME: {filename}\n"
        f"TOTAL SOURCE LINES: {len(original_code.splitlines())}\n"
        f"DETERMINISTIC VALIDATION: {syntax_context or 'No deterministic syntax result was supplied.'}\n"
        "--- BEGIN VERIFIED FINDINGS JSON ---\n"
        f"{verified_findings_json}\n"
        "--- END VERIFIED FINDINGS JSON ---\n"
        "--- BEGIN NUMBERED ORIGINAL SOURCE ---\n"
        f"{numbered_source}\n"
        "--- END NUMBERED ORIGINAL SOURCE ---\n"
        "Return the smallest complete set of non-overlapping JSON line-range edits needed to correct every "
        "confirmed finding. Do not change unrelated formatting or declarations."
    )

# Language-specific audit guidance keeps the model anchored to the submitted grammar
# instead of defaulting to Python-like assumptions.
LANGUAGE_REVIEW_GUIDANCE = {
    "py": "Python 3 grammar, indentation, imports, name binding, exceptions, async behavior, mutability, and runtime control flow.",
    "js": "Modern JavaScript/ECMAScript modules, async promises, closures, scope, DOM/Node APIs, undefined references, coercion, and runtime control flow.",
    "jsx": "JavaScript plus JSX element syntax, component props, hook rules visible in the source, event handlers, and rendering control flow.",
    "ts": "TypeScript syntax and static types, nullability, generics, narrowing, module boundaries, async behavior, and emitted JavaScript runtime behavior.",
    "tsx": "TypeScript plus TSX/React element syntax, props, hooks visible in the source, nullability, and component rendering behavior.",
    "java": "Java syntax, types, checked exceptions, object lifetime, null handling, collection use, concurrency, and compile-time symbol correctness.",
    "c": "ISO C syntax, declarations, pointer validity, array bounds, ownership, undefined behavior, format strings, and resource lifetime.",
    "cpp": "Modern C++ syntax, templates, references, ownership/RAII, iterator validity, undefined behavior, exceptions, and lifetime safety.",
    "h": "C/C++ header syntax, declarations, include guards, linkage, type completeness, and API consistency.",
    "hpp": "C++ header syntax, declarations, templates, include guards, linkage, type completeness, and API consistency.",
    "go": "Go syntax, package rules, error handling, goroutines, channels, defer behavior, interfaces, slices/maps, and resource lifetime.",
    "rb": "Ruby syntax, blocks, method lookup, nil handling, exceptions, mutation, and observable runtime behavior.",
    "php": "Modern PHP syntax, variables, arrays, types, namespaces, exceptions, request data, SQL/output escaping, and runtime behavior.",
    "cs": "C# syntax, nullable references, async/await, LINQ, disposal, exceptions, generics, and compile-time symbol correctness.",
    "rs": "Rust syntax, ownership, borrowing, lifetimes visible in the source, Result/Option handling, panics, concurrency, and unsafe blocks.",
    "swift": "Swift syntax, optionals, value/reference semantics, error handling, concurrency, collection bounds, and framework API use.",
    "kt": "Kotlin syntax, null safety, coroutines, collections, smart casts, exceptions, and Java interop visible in the source.",
    "sql": "SQL statement grammar, aliases, joins, grouping, aggregation, parameterization, null semantics, data-changing predicates, and transaction safety.",
    "sh": "POSIX/Bash syntax, quoting, expansions, pipelines, exit status, set -e interactions, file paths, and destructive commands.",
    "html": "HTML document and fragment structure, tag nesting, attributes, form semantics, references, accessibility defects with concrete impact, and embedded resource correctness.",
    "css": "CSS selector and declaration grammar, at-rules, custom properties, cascade, specificity, invalid tokens/properties, layout contradictions, and browser-visible behavior.",
    "txt": "Treat the input as plain text and report only clearly embedded code defects.",
}

COMPACT_AUDIT_SYSTEM_INSTRUCTION = """You are CORE Polyglot Audit, a deterministic senior code reviewer.
You must review the exact submitted programming language; never translate it into Python or apply Python syntax rules.
Return one JSON object only with this schema:
{
  "verdict": "CLEAN" or "ISSUES",
  "findings": [
    {
      "severity": "Critical" or "Warning",
      "line": "exact 1-based line number or range",
      "symbol": "exact token, selector, function, class, query, or declaration from the source",
      "cause": "directly provable defect",
      "impact": "concrete observable consequence",
      "correction": "precise required correction"
    }
  ]
}
Rules:
- Inspect the complete source line by line using the submitted language's grammar and semantics.
- Deterministic parser/compiler diagnostics are authoritative and must be retained.
- Report syntax, compile-time, definite runtime, logic, security, reliability, and material performance defects only.
- Do not report style preferences, optional refactors, hypothetical risks, or missing requirements that are not visible.
- Every finding must identify a real line/range and a source symbol/token that exists in the submitted code.
- CLEAN is allowed only when no directly provable defect exists.
- Do not return corrected code, Markdown, greetings, commentary, or text outside the JSON object."""

COMPACT_VERIFY_SYSTEM_INSTRUCTION = """You are CORE Polyglot Verify, an independent principal engineer.
Reinspect the full original source in its exact submitted language and verify the candidate findings.
Return one JSON object only using the same verdict/findings schema.
- Keep every directly provable defect and deterministic diagnostic.
- Remove style advice, speculation, duplicate claims, and findings whose line or symbol is not grounded in the source.
- Add a definite defect only when its exact line/range and source symbol can be identified.
- Never return CLEAN while a deterministic parser/compiler diagnostic remains.
- Do not return corrected code or commentary."""

COMPACT_REPAIR_SYSTEM_INSTRUCTION = """You are CORE Polyglot Repair, a deterministic source correction engine.
Apply only the verified findings to the exact submitted programming language.
Preserve unrelated behavior, public interfaces, names, comments, formatting, and file structure wherever practical.
Return the complete corrected file between these exact markers and nothing else:
<<<BEGIN_COMPLETE_SOURCE>>>
[complete corrected source]
<<<END_COMPLETE_SOURCE>>>
Never return a diff, excerpt, placeholder, omitted section, Markdown fence, explanation, or another programming language."""


def language_review_guidance(language: str) -> str:
    return LANGUAGE_REVIEW_GUIDANCE.get(
        language,
        "Use the exact submitted language grammar, compiler rules, and runtime semantics.",
    )


def build_compact_analysis_prompt(
    code: str,
    language: str,
    filename: str,
    focus: str,
    detail: str,
    syntax_context: str,
) -> str:
    return (
        f"LANGUAGE ID: {language}\n"
        f"LANGUAGE RULES: {language_review_guidance(language)}\n"
        f"FILENAME: {filename}\n"
        f"REVIEW FOCUS: {FOCUS_GUIDANCE.get(focus, FOCUS_GUIDANCE['balanced'])}\n"
        f"DETAIL LEVEL: {DETAIL_GUIDANCE.get(detail, DETAIL_GUIDANCE['standard'])}\n"
        f"DETERMINISTIC VALIDATION: {syntax_context or 'No deterministic syntax result was supplied.'}\n"
        "Review the complete source. Return only the compact JSON verdict and evidence-grounded findings.\n"
        "--- BEGIN COMPLETE SOURCE ---\n"
        f"{code}\n"
        "--- END COMPLETE SOURCE ---"
    )


def build_compact_verification_prompt(
    original_code: str,
    language: str,
    filename: str,
    syntax_context: str,
    candidate_findings_json: str,
) -> str:
    return (
        f"LANGUAGE ID: {language}\n"
        f"LANGUAGE RULES: {language_review_guidance(language)}\n"
        f"FILENAME: {filename}\n"
        f"DETERMINISTIC VALIDATION: {syntax_context or 'No deterministic syntax result was supplied.'}\n"
        "--- BEGIN COMPLETE ORIGINAL SOURCE ---\n"
        f"{original_code}\n"
        "--- END COMPLETE ORIGINAL SOURCE ---\n"
        "--- BEGIN CANDIDATE FINDINGS JSON ---\n"
        f"{candidate_findings_json}\n"
        "--- END CANDIDATE FINDINGS JSON ---\n"
        "Verify every candidate finding against the source and return only the final compact JSON verdict."
    )


def build_compact_repair_prompt(
    original_code: str,
    language: str,
    filename: str,
    verified_findings_json: str,
    syntax_context: str,
) -> str:
    return (
        f"LANGUAGE ID: {language}\n"
        f"LANGUAGE RULES: {language_review_guidance(language)}\n"
        f"FILENAME: {filename}\n"
        f"DETERMINISTIC VALIDATION: {syntax_context or 'No deterministic syntax result was supplied.'}\n"
        "--- BEGIN VERIFIED FINDINGS JSON ---\n"
        f"{verified_findings_json}\n"
        "--- END VERIFIED FINDINGS JSON ---\n"
        "--- BEGIN COMPLETE ORIGINAL SOURCE ---\n"
        f"{original_code}\n"
        "--- END COMPLETE ORIGINAL SOURCE ---\n"
        "Return the complete corrected source between the exact required markers."
    )
