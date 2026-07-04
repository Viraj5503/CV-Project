"""Streamlit demo UI for the PCB defect-detection service.

Talks to the FastAPI backend (``PCB_API_URL``, default http://localhost:8000):
upload a board photo -> original vs annotated side by side, detection table,
optional Claude-written inspection report. Degrades gracefully when the
Anthropic key is missing or out of credits — detection never depends on it.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import requests
import streamlit as st

API_URL = os.environ.get("PCB_API_URL", "http://localhost:8000").rstrip("/")
SAMPLES_DIR = Path(__file__).parent / "samples"

# Palette: the board's own materials (see .streamlit/config.toml for the rest)
COPPER = "#C87941"
SILKSCREEN = "#E8EDE8"
MUTED = "#8FA396"
LED_UP = "#4ADE80"
LED_DOWN = "#F87171"

st.set_page_config(page_title="PCB Inspect", page_icon="🔬", layout="wide")


# ---------------------------------------------------------------- API client


def api_is_up() -> bool:
    try:
        resp = requests.get(f"{API_URL}/health", timeout=2)
        return resp.status_code == 200 and resp.json().get("status") == "ok"
    except requests.RequestException:
        return False


@st.cache_data(show_spinner=False)
def inspect(image_bytes: bytes, filename: str, conf: float, with_report: bool) -> dict:
    """POST the image to /inspect; cached so reruns don't repeat identical calls."""
    resp = requests.post(
        f"{API_URL}/inspect",
        params={"conf": conf, "with_report": with_report},
        files={"image": (filename, image_bytes)},
        timeout=300,  # CPU inference in Docker takes seconds; a report adds a Claude call
    )
    resp.raise_for_status()
    return resp.json()


# --------------------------------------------------- title block (signature)


def render_titleblock(up: bool) -> None:
    """Silkscreen-style title block; the LED shows live API health."""
    led = LED_UP if up else LED_DOWN
    st.markdown(
        f"""
        <style>
        .titleblock {{
            display: flex; align-items: center; gap: 0.9rem;
            border: 1px solid {COPPER}55; border-radius: 4px;
            padding: 0.85rem 1.1rem; margin-bottom: 0.6rem;
            font-family: "Source Code Pro", monospace;
        }}
        .tb-led {{
            width: 10px; height: 10px; border-radius: 50%; flex: none;
            background: {led}; box-shadow: 0 0 8px {led};
        }}
        .tb-name {{
            font-size: 1.3rem; font-weight: 700;
            letter-spacing: 0.18em; color: {SILKSCREEN};
        }}
        .tb-sub {{
            font-size: 0.7rem; letter-spacing: 0.14em;
            color: {MUTED}; margin-top: 2px;
        }}
        .tb-right {{
            margin-left: auto; text-align: right;
            font-size: 0.7rem; letter-spacing: 0.14em; color: {MUTED};
        }}
        </style>
        <div class="titleblock">
            <div class="tb-led"></div>
            <div>
                <div class="tb-name">PCB-INSPECT</div>
                <div class="tb-sub">AUTOMATED OPTICAL INSPECTION &middot; YOLO11S &middot; 6 DEFECT CLASSES</div>
            </div>
            <div class="tb-right">API {"ONLINE" if up else "OFFLINE"}<br>REV A</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------- sidebar

with st.sidebar:
    st.header("Controls")
    conf = st.slider(
        "Confidence threshold",
        min_value=0.05,
        max_value=0.95,
        value=0.25,
        step=0.05,
        help="Detections below this confidence are dropped.",
    )
    with_report = st.toggle(
        "AI inspection report",
        value=False,
        help=(
            "Claude reviews the board photo and writes severity, likely cause and "
            "rework steps per defect. Needs ANTHROPIC_API_KEY with credits — "
            "see .env.example."
        ),
    )
    st.divider()
    st.caption(f"API · {API_URL}")

# ---------------------------------------------------------------------- main

api_up = api_is_up()
render_titleblock(api_up)

if not api_up:
    st.error(
        f"Detection service is not responding at {API_URL}.\n\n"
        "Start it with `uvicorn pcb_vision.api:app` (or `docker compose up`), "
        "then reload this page."
    )
    st.stop()

upload_col, sample_col = st.columns([3, 2], vertical_alignment="bottom")
with upload_col:
    uploaded = st.file_uploader("Board photo", type=["jpg", "jpeg", "png", "webp"])
with sample_col:
    sample_names = sorted(p.name for p in SAMPLES_DIR.glob("*.jpg"))
    sample_choice = st.selectbox(
        "…or pick a sample board", ["(none)"] + sample_names,
        help="Test-split boards the model has never trained on.",
    )

if uploaded is not None:  # an upload wins over the sample picker
    image_bytes, image_name = uploaded.getvalue(), uploaded.name
elif sample_choice != "(none)":
    sample_path = SAMPLES_DIR / sample_choice
    image_bytes, image_name = sample_path.read_bytes(), sample_choice
else:
    st.info("Upload a board photo to inspect it — or pick a sample board.")
    st.stop()

try:
    with st.spinner("Inspecting board…"):
        result = inspect(image_bytes, image_name, conf, with_report)
except requests.RequestException as exc:
    st.error(f"Inspection request failed: {exc}")
    st.stop()

detections = result["detections"]

original_col, annotated_col = st.columns(2)
with original_col:
    st.image(image_bytes, caption=f"SOURCE · {image_name}", width="stretch")
with annotated_col:
    st.image(
        base64.standard_b64decode(result["annotated_image_b64"]),
        caption="DETECTIONS",
        width="stretch",
    )

count_col, latency_col, top_col = st.columns(3)
count_col.metric("Defects found", len(detections))
latency_col.metric("Inference time", f'{result["inference_ms"]:.0f} ms')
top_conf = max((d["confidence"] for d in detections), default=None)
top_col.metric("Top confidence", f"{top_conf:.2f}" if top_conf is not None else "—")

if not detections:
    st.success("No defects detected at this threshold — board passes.")
else:
    st.dataframe(
        [
            {
                "defect": d["class_name"].replace("_", " "),
                "confidence": d["confidence"],
                "box": str(d["box_xyxy"]),
            }
            for d in detections
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "defect": st.column_config.TextColumn("Defect"),
            "confidence": st.column_config.ProgressColumn(
                "Confidence", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "box": st.column_config.TextColumn("Box [x1, y1, x2, y2]"),
        },
    )

if with_report:
    if result["report"]:
        with st.expander("AI inspection report", expanded=True):
            st.markdown(result["report"])
    else:
        st.warning(
            "AI report unavailable — the detection results above are unaffected. "
            "Reports need an Anthropic API key with credits: copy `.env.example` "
            "to `.env`, set `ANTHROPIC_API_KEY`, and restart the API."
        )
        if result.get("report_error"):
            st.caption(f"API said: {result['report_error']}")
