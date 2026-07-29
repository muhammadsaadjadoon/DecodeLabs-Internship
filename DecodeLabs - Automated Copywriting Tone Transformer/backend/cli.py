#!/usr/bin/env python
"""
CLI entry point for the Lexora AI Tone Studio.

Example:
    python cli.py --product "Aurora Earbuds" \\
                   --description "Noise-cancelling earbuds, 30h battery" \\
                   --platform linkedin --tone witty \\
                   --temperature 0.7 --top-p 0.9 +verbose

Notes on the argparse setup (per the training deck's CLI slide):
  - prefix_chars="-+" lets us tell standard flags (-o/--output) apart
    from custom actions (+verbose) at a glance.
  - platform_type / tone_type / unit_float_type are custom type
    converters: argparse calls them on the raw string and hands the
    parsed, validated value straight to the rest of the program instead
    of a bare string.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.gemini_client import GeminiTransientError, generate_copy
from app.models import GenerationRequest, GenerationResponse, Platform, Tone
from app.prompt_engine import compile_master_template


def platform_type(raw: str) -> Platform:
    try:
        return Platform(raw.strip().lower())
    except ValueError:
        valid = ", ".join(p.value for p in Platform)
        raise argparse.ArgumentTypeError(f"'{raw}' is not a valid platform. Choose from: {valid}")


def tone_type(raw: str) -> Tone:
    try:
        return Tone(raw.strip().lower())
    except ValueError:
        valid = ", ".join(t.value for t in Tone)
        raise argparse.ArgumentTypeError(f"'{raw}' is not a valid tone. Choose from: {valid}")


def unit_float_type(raw: str) -> float:
    value = float(raw)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError(f"top-p must be between 0.0 and 1.0, got {value}")
    return value


def temperature_type(raw: str) -> float:
    value = float(raw)
    if not 0.0 <= value <= 2.0:
        raise argparse.ArgumentTypeError(f"temperature must be between 0.0 and 2.0, got {value}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Generate platform-tuned marketing copy from the command line.",
        prefix_chars="-+",
    )
    parser.add_argument("--product", required=True, help="Product name")
    parser.add_argument("--description", required=True, help="Raw product description / facts")
    parser.add_argument("--platform", required=True, type=platform_type, help="linkedin | instagram | email | twitter")
    parser.add_argument("--tone", required=True, type=tone_type, help="witty | professional | bold | friendly | luxury | urgent")
    parser.add_argument("--temperature", type=temperature_type, default=0.7, help="Model creativity, 0.0-2.0 (default 0.7)")
    parser.add_argument("--top-p", dest="top_p", type=unit_float_type, default=0.9, help="Nucleus sampling, 0.0-1.0 (default 0.9)")
    parser.add_argument("-o", "--output", help="Write JSON result to this file instead of stdout")
    # Custom '+' prefixed action, distinct from standard '-' flags
    parser.add_argument("+verbose", "+v", dest="verbose", action="store_true", help="Print the compiled prompt before generating")
    return parser


async def _run(args: argparse.Namespace) -> GenerationResponse:
    request = GenerationRequest(
        product_name=args.product,
        product_description=args.description,
        platform=args.platform,
        tone=args.tone,
        temperature=args.temperature,
        top_p=args.top_p,
    )
    prompt = compile_master_template(request)
    if args.verbose:
        print("--- Compiled Master Instruction Template ---", file=sys.stderr)
        print(prompt, file=sys.stderr)
        print("---------------------------------------------", file=sys.stderr)

    copy = await generate_copy(prompt, request.temperature, request.top_p)
    return GenerationResponse.build(request, copy)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        response = asyncio.run(_run(args))
    except GeminiTransientError as exc:
        print(f"Generation failed after retries: {exc}", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(response.model_dump(mode="json"), indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
