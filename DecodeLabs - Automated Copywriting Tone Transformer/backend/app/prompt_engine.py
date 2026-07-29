"""
Lexora prompt compiler.

The frontend sends only user-controlled brief fields. This module converts the
brief into a controlled server-side instruction with brand safety, platform
formatting, transformation modes, and fixed variation requirements.
"""
from __future__ import annotations

from app.models import PLATFORM_CONSTRAINTS, GenerationRequest, Platform, Tone, TransformMode

_BRAND_SAFETY_GUIDELINES = (
    "Never invent numeric claims, statistics, awards, certifications, prices, "
    "medical/legal/financial guarantees, or competitor comparisons that were "
    "not explicitly provided. Never disparage competitors by name. Never use "
    "discriminatory, explicit, or profane language. Keep claims realistic and useful."
)

_TONE_GUIDANCE: dict[Tone, str] = {
    Tone.WITTY: "clever, playful, quick wordplay, light humor, never corny",
    Tone.PROFESSIONAL: "polished, precise, confident, zero slang",
    Tone.BOLD: "punchy, high-energy, short declarative sentences",
    Tone.FRIENDLY: "warm, conversational, approachable, second person",
    Tone.LUXURY: "understated, refined, sensory, aspirational restraint",
    Tone.URGENT: "time-pressured, action-first, scarcity-driven without false scarcity",
    Tone.ENERGETIC: "fast, enthusiastic, vivid, motivational, action-heavy",
    Tone.EMPATHETIC: "understanding, warm, supportive, emotionally aware",
    Tone.CONFIDENT: "clear, assured, benefit-led, credible, no hype overload",
}

_PLATFORM_GUIDANCE: dict[Platform, str] = {
    Platform.LINKEDIN: "Professional structure: hook, context, value, clear CTA, optional 3-5 hashtags.",
    Platform.INSTAGRAM: "Caption style: visual hook, skimmable lines, CTA, 5-10 discoverable hashtags.",
    Platform.FACEBOOK: "Conversational style: friendly opening, simple value, natural CTA, light hashtags.",
    Platform.EMAIL: "Email style: headline acts like subject, body is skimmable, no hashtags, one CTA.",
    Platform.TWITTER: "X style: concise post, combined headline + body + CTA within 280 chars, max 2 hashtags.",
    Platform.GOOGLE_ADS: "Google Ads style: short benefit-led headline and compact description. No hashtags.",
    Platform.YOUTUBE: "YouTube style: title-like headline, description body, tags/hashtags if useful.",
    Platform.TIKTOK: "TikTok style: strong hook, short caption, social-native CTA, trend-aware hashtags.",
}

_MODE_GUIDANCE: dict[TransformMode, str] = {
    TransformMode.GENERATE: "Generate fresh marketing copy from the product facts.",
    TransformMode.REWRITE: "Rewrite the supplied source text while preserving meaning.",
    TransformMode.SHORTEN: "Make the supplied source text shorter and clearer.",
    TransformMode.EXPAND: "Expand the supplied source text with useful detail without inventing facts.",
    TransformMode.IMPROVE: "Improve clarity, flow, persuasion, and structure.",
    TransformMode.SIMPLIFY: "Simplify the text so a general audience can understand it quickly.",
    TransformMode.HUMANIZE: "Make the text sound natural, human, and less robotic.",
    TransformMode.GRAMMAR_FIX: "Fix grammar, spelling, punctuation, and flow without changing meaning.",
    TransformMode.MAKE_PROFESSIONAL: "Make the text more polished, professional, and business-ready.",
    TransformMode.CHANGE_TONE: "Transform the text into the selected tone while preserving the core message.",
    TransformMode.HEADLINES: "Generate headline options. Use body for short rationale or supporting line.",
    TransformMode.HASHTAGS: "Generate hashtag-focused output. Use body to explain grouping if needed.",
    TransformMode.TRANSLATE: "Translate or localize the text into the requested language while keeping intent.",
}


def _brand_profile_block(request: GenerationRequest) -> str:
    profile = request.brand_voice_profile
    parts: list[str] = []
    if request.brand_voice:
        parts.append(f"Brand voice notes: {request.brand_voice}")
    if profile:
        if profile.brand_description:
            parts.append(f"Brand description: {profile.brand_description}")
        if profile.preferred_tone:
            parts.append(f"Preferred tone: {profile.preferred_tone}")
        if profile.vocabulary:
            parts.append(f"Preferred vocabulary: {profile.vocabulary}")
        if profile.words_to_avoid:
            parts.append(f"Words to avoid: {profile.words_to_avoid}")
        if profile.audience_notes:
            parts.append(f"Audience notes: {profile.audience_notes}")
        if profile.cta_style:
            parts.append(f"CTA style: {profile.cta_style}")
        if profile.example_copy:
            parts.append(f"Example brand copy to emulate: {profile.example_copy}")
    if not parts:
        return "No custom brand voice profile was supplied. Use a clean, premium SaaS voice."
    return "\n".join(f"- {part}" for part in parts)


def compile_master_template(request: GenerationRequest) -> str:
    constraints = PLATFORM_CONSTRAINTS[request.platform]
    tone_guidance = _TONE_GUIDANCE[request.tone]
    platform_guidance = _PLATFORM_GUIDANCE[request.platform]
    mode_guidance = _MODE_GUIDANCE[request.transform_mode]
    custom_cta = f"Custom CTA preference: {request.custom_cta}" if request.custom_cta else "No custom CTA text supplied."
    source_text = request.source_text or "No source text supplied; generate from product facts."

    template = f"""You are Lexora, a premium AI copywriting and tone transformation engine.

TASK MODE:
{request.transform_mode.value} — {mode_guidance}

BRAND SAFETY GUIDELINES (never break these):
{_BRAND_SAFETY_GUIDELINES}

PRODUCT / OFFER FACTS:
- Product name: {request.product_name}
- Product description: {request.product_description}
- Target audience: {request.target_audience}
- Content objective: {request.content_objective.value}
- Requested language: {request.language}
- Copy length: {request.copy_length.value}
- Keywords to include naturally: {request.keywords or 'None'}
- Emoji level: {request.emoji_level.value}
- Formality level: {request.formality_level.value}
- CTA type: {request.cta_type.value}
- {custom_cta}

SOURCE TEXT FOR TRANSFORMATION MODES:
{source_text}

BRAND VOICE PROFILE:
{_brand_profile_block(request)}

TONE:
{request.tone.value} — {tone_guidance}

TARGET PLATFORM:
{constraints['label']} — {constraints['format']}
{platform_guidance}

HARD CONSTRAINTS:
- Combined headline + body + call_to_action for each variation must not exceed {constraints['max_chars']} characters.
- {'Do not include hashtags for this platform.' if not constraints['supports_hashtags'] else 'Use hashtags only when they improve platform fit.'}
- Keep output in {request.language} unless a brand/product name must stay unchanged.
- If a requested keyword cannot fit naturally, do not force it.
- Do not include markdown fences, commentary, analysis, or explanations outside the JSON fields.

VARIATION REQUIREMENT:
Return exactly {request.number_of_variations} variations. If 3 variations are requested, name them exactly:
1. Safe — polished, reliable, low-risk, commercially usable.
2. Creative — more memorable and distinctive while still accurate.
3. Bold — stronger, punchier, more confident without false claims.

Return ONLY valid JSON that matches this schema:
{{
  "variations": [
    {{
      "style": "Safe",
      "headline": "...",
      "body": "...",
      "hashtags": ["#example"],
      "call_to_action": "..."
    }}
  ]
}}"""
    return template
