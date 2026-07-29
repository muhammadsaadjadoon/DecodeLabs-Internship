"""
Pydantic models for Lexora.

The public API now accepts a richer creative brief, returns multiple
controlled variations, and preserves strict validation before anything leaves
server-side code.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    EMAIL = "email"
    TWITTER = "twitter"
    GOOGLE_ADS = "google_ads"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"


class Tone(str, Enum):
    WITTY = "witty"
    PROFESSIONAL = "professional"
    BOLD = "bold"
    FRIENDLY = "friendly"
    LUXURY = "luxury"
    URGENT = "urgent"
    ENERGETIC = "energetic"
    EMPATHETIC = "empathetic"
    CONFIDENT = "confident"


class ContentObjective(str, Enum):
    SALES = "sales"
    AWARENESS = "awareness"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"
    EDUCATION = "education"
    LAUNCH = "launch"
    RETENTION = "retention"


class CopyLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class EmojiLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FormalityLevel(str, Enum):
    CASUAL = "casual"
    BALANCED = "balanced"
    FORMAL = "formal"


class CTAType(str, Enum):
    SHOP_NOW = "shop_now"
    LEARN_MORE = "learn_more"
    SIGN_UP = "sign_up"
    BOOK_DEMO = "book_demo"
    DOWNLOAD = "download"
    COMMENT = "comment"
    FOLLOW = "follow"
    CUSTOM = "custom"


class TransformMode(str, Enum):
    GENERATE = "generate"
    REWRITE = "rewrite"
    SHORTEN = "shorten"
    EXPAND = "expand"
    IMPROVE = "improve"
    SIMPLIFY = "simplify"
    HUMANIZE = "humanize"
    GRAMMAR_FIX = "grammar_fix"
    MAKE_PROFESSIONAL = "make_professional"
    CHANGE_TONE = "change_tone"
    HEADLINES = "headlines"
    HASHTAGS = "hashtags"
    TRANSLATE = "translate"


PLATFORM_CONSTRAINTS: dict[Platform, dict] = {
    Platform.TWITTER: {
        "max_chars": 280,
        "label": "X / Twitter",
        "supports_hashtags": True,
        "format": "single post with strict character discipline",
    },
    Platform.INSTAGRAM: {
        "max_chars": 2200,
        "label": "Instagram",
        "supports_hashtags": True,
        "format": "caption, visual hook, CTA, and hashtag set",
    },
    Platform.LINKEDIN: {
        "max_chars": 3000,
        "label": "LinkedIn",
        "supports_hashtags": True,
        "format": "professional hook, short paragraphs, insight, CTA",
    },
    Platform.FACEBOOK: {
        "max_chars": 3000,
        "label": "Facebook",
        "supports_hashtags": True,
        "format": "conversational post with natural CTA",
    },
    Platform.EMAIL: {
        "max_chars": 1500,
        "label": "Email",
        "supports_hashtags": False,
        "format": "subject, preview-style headline, body, CTA",
    },
    Platform.GOOGLE_ADS: {
        "max_chars": 450,
        "label": "Google Ads",
        "supports_hashtags": False,
        "format": "ad headline and description style copy",
    },
    Platform.YOUTUBE: {
        "max_chars": 5000,
        "label": "YouTube",
        "supports_hashtags": True,
        "format": "title, description, and tags-friendly copy",
    },
    Platform.TIKTOK: {
        "max_chars": 2200,
        "label": "TikTok",
        "supports_hashtags": True,
        "format": "hook, caption, CTA, and hashtags",
    },
}


class BrandVoice(BaseModel):
    brand_description: str = Field("", max_length=1000)
    preferred_tone: str = Field("", max_length=300)
    vocabulary: str = Field("", max_length=600)
    words_to_avoid: str = Field("", max_length=600)
    audience_notes: str = Field("", max_length=600)
    cta_style: str = Field("", max_length=300)
    example_copy: str = Field("", max_length=1800)

    @field_validator("brand_description", "preferred_tone", "vocabulary", "words_to_avoid", "audience_notes", "cta_style", "example_copy")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class GenerationRequest(BaseModel):
    """A rich Lexora generation/transform request."""

    product_name: str = Field(..., min_length=2, max_length=120)
    product_description: str = Field(..., min_length=10, max_length=2500)
    target_audience: str = Field("General buyers", max_length=300)
    content_objective: ContentObjective = ContentObjective.SALES
    language: str = Field("English", max_length=60)
    copy_length: CopyLength = CopyLength.MEDIUM
    keywords: str = Field("", max_length=500)
    brand_voice: str = Field("", max_length=1200)
    brand_voice_profile: Optional[BrandVoice] = None
    emoji_level: EmojiLevel = EmojiLevel.LOW
    number_of_variations: int = Field(3, ge=1, le=5)
    formality_level: FormalityLevel = FormalityLevel.BALANCED
    cta_type: CTAType = CTAType.LEARN_MORE
    custom_cta: str = Field("", max_length=160)
    transform_mode: TransformMode = TransformMode.GENERATE
    source_text: str = Field("", max_length=4000)
    platform: Platform
    tone: Tone
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)

    @field_validator(
        "product_name",
        "product_description",
        "target_audience",
        "language",
        "keywords",
        "brand_voice",
        "custom_cta",
        "source_text",
    )
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class GeneratedCopy(BaseModel):
    style: str = Field(..., description="Variation name, e.g. Safe, Creative, Bold")
    headline: str = Field(..., description="Short attention-grabbing hook")
    body: str = Field(..., description="Main marketing copy")
    hashtags: list[str] = Field(default_factory=list)
    call_to_action: str = Field(..., description="Single closing CTA line")


class GeneratedVariations(BaseModel):
    variations: list[GeneratedCopy] = Field(default_factory=list)


class OutputVariation(GeneratedCopy):
    char_count: int
    max_chars: int
    compliant: bool

    @classmethod
    def build(cls, req: GenerationRequest, copy: GeneratedCopy) -> "OutputVariation":
        full_text = f"{copy.headline} {copy.body} {copy.call_to_action}"
        char_count = len(full_text)
        max_chars = PLATFORM_CONSTRAINTS[req.platform]["max_chars"]
        return cls(
            style=copy.style,
            headline=copy.headline,
            body=copy.body,
            hashtags=copy.hashtags,
            call_to_action=copy.call_to_action,
            char_count=char_count,
            max_chars=max_chars,
            compliant=char_count <= max_chars,
        )


class GenerationResponse(BaseModel):
    platform: Platform
    tone: Tone
    variations: list[OutputVariation]
    copy: OutputVariation
    char_count: int
    max_chars: int
    compliant: bool
    temperature: float
    top_p: float

    @classmethod
    def build(cls, req: GenerationRequest, generated: GeneratedVariations | GeneratedCopy) -> "GenerationResponse":
        if isinstance(generated, GeneratedCopy):
            raw_variations = [generated]
        else:
            raw_variations = generated.variations or []
        if not raw_variations:
            raw_variations = [
                GeneratedCopy(
                    style="Safe",
                    headline="Generation complete",
                    body="Lexora generated content, but the model returned an empty variations list.",
                    hashtags=[],
                    call_to_action="Review and refine this copy.",
                )
            ]

        preferred_order = {"safe": 0, "creative": 1, "bold": 2}
        ordered = sorted(raw_variations, key=lambda item: preferred_order.get(item.style.lower(), 99))
        limit = max(1, min(req.number_of_variations, len(ordered)))
        variations = [OutputVariation.build(req, item) for item in ordered[:limit]]
        primary = variations[0]
        return cls(
            platform=req.platform,
            tone=req.tone,
            variations=variations,
            copy=primary,
            char_count=primary.char_count,
            max_chars=primary.max_chars,
            compliant=primary.compliant,
            temperature=req.temperature,
            top_p=req.top_p,
        )


class BulkRow(BaseModel):
    row_id: int
    product_name: str
    product_description: str
    target_audience: str = "General buyers"
    content_objective: ContentObjective = ContentObjective.SALES
    language: str = "English"
    copy_length: CopyLength = CopyLength.MEDIUM
    keywords: str = ""
    brand_voice: str = ""
    emoji_level: EmojiLevel = EmojiLevel.LOW
    number_of_variations: int = 3
    formality_level: FormalityLevel = FormalityLevel.BALANCED
    cta_type: CTAType = CTAType.LEARN_MORE
    platform: Platform
    tone: Tone
    temperature: float = 0.7
    top_p: float = 0.9


class BulkResult(BaseModel):
    row_id: int
    product_name: str
    status: str
    response: Optional[GenerationResponse] = None
    error: Optional[str] = None
