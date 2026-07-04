"""Tests for VLM inspection report generation (Anthropic API mocked)."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pcb_vision.report import MODEL, build_prompt, generate_report

DETECTIONS = [
    {"class_name": "missing_hole", "confidence": 0.91, "box_xyxy": [100, 200, 140, 240]},
    {"class_name": "spur", "confidence": 0.55, "box_xyxy": [300, 50, 330, 90]},
]

# 1x1 black pixel, valid PNG
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082"
)


@pytest.fixture
def image_path(tmp_path: Path) -> Path:
    p = tmp_path / "board.png"
    p.write_bytes(PNG_BYTES)
    return p


def make_client(stop_reason: str = "end_turn", text: str = "## Inspection Report") -> MagicMock:
    client = MagicMock()
    client.messages.create.return_value = SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=text)],
    )
    return client


class TestBuildPrompt:
    def test_lists_every_detection(self):
        prompt = build_prompt(DETECTIONS)
        assert "missing_hole" in prompt
        assert "spur" in prompt
        assert "0.91" in prompt
        assert "[100, 200, 140, 240]" in prompt

    def test_requests_structured_sections(self):
        prompt = build_prompt(DETECTIONS).lower()
        for section in ("summary", "severity", "likely cause", "recommended action"):
            assert section in prompt

    def test_handles_no_detections(self):
        prompt = build_prompt([]).lower()
        assert "no defects" in prompt


class TestGenerateReport:
    def test_sends_image_and_prompt(self, image_path: Path):
        client = make_client()
        generate_report(image_path, DETECTIONS, client=client)

        client.messages.create.assert_called_once()
        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["model"] == MODEL
        image_block, text_block = kwargs["messages"][0]["content"]
        assert image_block["type"] == "image"
        assert image_block["source"]["type"] == "base64"
        assert image_block["source"]["media_type"] == "image/png"
        assert len(image_block["source"]["data"]) > 0
        assert "missing_hole" in text_block["text"]

    def test_jpeg_media_type(self, tmp_path: Path):
        p = tmp_path / "board.jpg"
        p.write_bytes(PNG_BYTES)  # content irrelevant; media type comes from suffix
        client = make_client()
        generate_report(p, DETECTIONS, client=client)
        image_block = client.messages.create.call_args.kwargs["messages"][0]["content"][0]
        assert image_block["source"]["media_type"] == "image/jpeg"

    def test_returns_response_text(self, image_path: Path):
        client = make_client(text="## Inspection Report\n\nAll good.")
        report = generate_report(image_path, DETECTIONS, client=client)
        assert report == "## Inspection Report\n\nAll good."

    def test_refusal_raises(self, image_path: Path):
        client = make_client(stop_reason="refusal")
        with pytest.raises(RuntimeError, match="refused"):
            generate_report(image_path, DETECTIONS, client=client)
