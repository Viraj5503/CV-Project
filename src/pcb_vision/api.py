"""FastAPI service: PCB defect detection with optional Claude inspection report.

Endpoints:
    GET  /health   -> {"status": "ok", "model_loaded": bool}
    POST /inspect  -> detections + annotated image (base64 JPEG) + optional report
"""

from __future__ import annotations

import base64
import io
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

from pcb_vision.report import generate_report

MODEL_PATH = Path(os.environ.get("PCB_MODEL_PATH", "models/best.pt"))
DEVICE = os.environ.get("PCB_DEVICE")  # None -> ultralytics auto-selects (mps/cuda/cpu)
IMGSZ = 1024  # defects are ~45px on ~3000px boards; must match training resolution

_model = None


def get_model():
    """Load the YOLO model once and cache it."""
    global _model
    if _model is None:
        from ultralytics import YOLO  # deferred: import is slow, tests never need it

        _model = YOLO(MODEL_PATH)
    return _model


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_model()  # fail fast at startup if weights are missing
    yield


app = FastAPI(title="PCB Defect Detection API", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": _model is not None}


@app.post("/inspect")
async def inspect(
    image: UploadFile = File(...),
    conf: float = 0.25,
    with_report: bool = False,
) -> dict:
    raw = await image.read()
    try:
        pil = Image.open(io.BytesIO(raw))
        pil.load()
    except Exception:
        raise HTTPException(status_code=422, detail="Uploaded file is not a readable image")
    pil = pil.convert("RGB")

    t0 = perf_counter()
    result = get_model().predict(pil, imgsz=IMGSZ, conf=conf, device=DEVICE, verbose=False)[0]
    inference_ms = (perf_counter() - t0) * 1000

    detections = [
        {
            "class_name": result.names[int(box.cls)],
            "confidence": round(float(box.conf), 4),
            "box_xyxy": [round(v) for v in box.xyxy[0].tolist()],
        }
        for box in result.boxes
    ]

    annotated_bgr = result.plot()
    buf = io.BytesIO()
    Image.fromarray(annotated_bgr[..., ::-1]).save(buf, format="JPEG", quality=90)
    annotated_b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    report = None
    if with_report:
        # generate_report reads from a path; hand it the upload re-encoded as JPEG
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            pil.save(tmp, format="JPEG", quality=95)
            tmp_path = Path(tmp.name)
        try:
            report = generate_report(tmp_path, detections)
        finally:
            tmp_path.unlink(missing_ok=True)

    return {
        "detections": detections,
        "annotated_image_b64": annotated_b64,
        "report": report,
        "inference_ms": round(inference_ms, 1),
    }
