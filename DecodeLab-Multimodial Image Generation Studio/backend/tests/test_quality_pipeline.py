import base64
import json
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from main import GenerateIn
from quality_pipeline import extract_asset_from_json_file, moderate_input_text, validate_and_normalize_image


def test_strict_generation_enums_reject_unknown_values():
    with pytest.raises(ValidationError):
        GenerateIn(
            prompt="test image",
            mode="bogus",
            style="bogus",
            aspect_ratio="100:1",
        )


def test_ratio_resolution_conflict_is_rejected():
    with pytest.raises(ValidationError):
        GenerateIn(
            prompt="test image",
            aspect_ratio="9:16",
            resolution="1024x1024",
        )


def test_input_safety_gate_rejects_explicit_prompt():
    decision = moderate_input_text("give an image of a nude girl without dress")
    assert decision.allowed is False
    assert decision.code == "INPUT_SAFETY_REJECTED"


def test_base64_payload_is_decoded_to_disk(tmp_path: Path):
    payload = b"streamed-image-payload"
    response_file = tmp_path / "response.json"
    response_file.write_text(json.dumps({"result": {"image": base64.b64encode(payload).decode("ascii")}}))
    image_file = extract_asset_from_json_file(response_file, tmp_path)
    assert image_file.read_bytes() == payload


def test_output_is_normalized_to_requested_canvas(tmp_path: Path):
    source = tmp_path / "source.png"
    Image.new("RGB", (640, 640), "navy").save(source)
    validated = validate_and_normalize_image(source, 768, 1344, tmp_path)
    assert (validated.width, validated.height) == (768, 1344)
    assert validated.dimension_adjusted is True
    assert "normalized" in validated.dimension_warning
