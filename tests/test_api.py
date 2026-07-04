"""Tests for the FastAPI inspection service (YOLO model and Anthropic API mocked)."""

import base64
import io
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient
from PIL import Image

import pcb_vision.api as api


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buf, format="PNG")
    return buf.getvalue()


PNG_BYTES = _png_bytes()


def make_fake_model() -> MagicMock:
    """A stand-in for ultralytics.YOLO exposing the attrs api.py reads."""
    # torch tensors, same shapes ultralytics Boxes yield when iterated
    box = SimpleNamespace(
        cls=torch.tensor([0.0]),
        conf=torch.tensor([0.91]),
        xyxy=torch.tensor([[100.4, 200.2, 140.9, 240.1]]),
    )
    result = SimpleNamespace(
        names={0: "missing_hole"},
        boxes=[box],
        plot=lambda: np.zeros((16, 16, 3), dtype=np.uint8),  # BGR annotated image
    )
    model = MagicMock()
    model.predict.return_value = [result]
    return model


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "_model", make_fake_model())
    return TestClient(api.app)


class TestHealth:
    def test_reports_ok_with_model_loaded(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "model_loaded": True}


class TestInspect:
    def test_returns_detections_and_annotated_image(self, client: TestClient):
        resp = client.post("/inspect", files={"image": ("board.png", PNG_BYTES, "image/png")})
        assert resp.status_code == 200
        body = resp.json()
        assert body["detections"] == [
            {"class_name": "missing_hole", "confidence": 0.91, "box_xyxy": [100, 200, 141, 240]}
        ]
        assert body["report"] is None
        assert isinstance(body["inference_ms"], float) and body["inference_ms"] >= 0
        # annotated image must round-trip base64 into non-empty JPEG bytes
        annotated = base64.standard_b64decode(body["annotated_image_b64"])
        assert annotated[:2] == b"\xff\xd8"  # JPEG magic

    def test_conf_query_param_forwarded_to_model(self, client: TestClient, monkeypatch):
        fake = make_fake_model()
        monkeypatch.setattr(api, "_model", fake)
        client.post("/inspect?conf=0.5", files={"image": ("b.png", PNG_BYTES, "image/png")})
        assert fake.predict.call_args.kwargs["conf"] == 0.5

    def test_with_report_calls_generator(self, client: TestClient, monkeypatch):
        monkeypatch.setattr(api, "generate_report", lambda path, dets: "## Report")
        resp = client.post(
            "/inspect?with_report=true", files={"image": ("b.png", PNG_BYTES, "image/png")}
        )
        assert resp.status_code == 200
        assert resp.json()["report"] == "## Report"

    def test_rejects_non_image_upload(self, client: TestClient):
        resp = client.post("/inspect", files={"image": ("notes.txt", b"hello", "text/plain")})
        assert resp.status_code == 422

    def test_rejects_missing_file_field(self, client: TestClient):
        resp = client.post("/inspect")
        assert resp.status_code == 422
