"""Strict API contracts shared by the CodeFix AI analysis pipeline."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


ReviewFocus = Literal["balanced", "correctness", "security", "performance"]
DetailLevel = Literal["concise", "standard", "deep"]
ThemeMode = Literal["dark", "light"]


class ReviewResponse(BaseModel):
    filename: str
    language: str
    bug_report: str = Field(..., description="Markdown bullet list of verified findings")
    refactored_code: str = Field(..., description="Complete corrected source code")
    has_issues: bool
    model_used: str


class ExplainRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100_000)
    language: str = Field(default="text", min_length=1, max_length=40)
    filename: str = Field(default="reviewed-code.txt", min_length=1, max_length=255)
    detail: DetailLevel = "standard"
    session_id: Optional[str] = Field(default=None, max_length=80)


class ExplainResponse(BaseModel):
    filename: str
    language: str
    explanation: str
    model_used: str


class ProfileSettings(BaseModel):
    name: str = Field(default="", max_length=80)
    role: str = Field(default="", max_length=100)


class WorkspaceSettingsUpdate(BaseModel):
    profile: ProfileSettings
    focus: ReviewFocus = "balanced"
    detail: DetailLevel = "standard"
    auto_explain: bool = False
    theme: ThemeMode = "dark"


class ErrorResponse(BaseModel):
    detail: str
