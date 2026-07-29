from app.models import GenerationRequest, Platform, Tone
from app.prompt_engine import compile_master_template


def test_prompt_includes_advanced_controls():
    req = GenerationRequest(
        product_name="Aurora Earbuds",
        product_description="Wireless earbuds with 30-hour battery life.",
        target_audience="University students",
        platform=Platform.INSTAGRAM,
        tone=Tone.ENERGETIC,
        keywords="study, commute",
    )
    prompt = compile_master_template(req)
    assert "University students" in prompt
    assert "study, commute" in prompt
    assert "Safe" in prompt and "Creative" in prompt and "Bold" in prompt
