"""AI-written PCB inspection reports from YOLO detections via Claude vision.

Sends the inspected board image plus the detector's findings to Claude and
returns a structured markdown report (summary, per-defect severity/location/
likely cause, recommended action).
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()  # pull ANTHROPIC_API_KEY / PCB_VLM_MODEL from .env into the environment

MODEL = os.environ.get("PCB_VLM_MODEL", "claude-opus-4-8")
MAX_TOKENS = 4096  # a report is short; deliberately capped

MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

PROMPT_TEMPLATE = """\
You are a PCB quality-inspection engineer. The attached image is a bare PCB \
that was analyzed by an automated defect detector. Detected defects \
(pixel coordinates are [x1, y1, x2, y2] boxes on the attached image):

{detections}

Write a concise inspection report in markdown with exactly these sections:

## Summary
One short paragraph: overall board condition and defect count.

## Defect Analysis
For each detected defect, a subsection with:
- **Severity**: critical / major / minor, judged from defect type and what it affects
- **Location**: where on the board (refer to the image, not just coordinates)
- **Likely cause**: the most probable manufacturing cause

## Recommended Action
Whether the board should be scrapped, reworked, or passed, and the specific \
rework steps if applicable.
"""


def build_prompt(detections: list[dict]) -> str:
    """Render the report prompt for a list of detections.

    Each detection: {"class_name": str, "confidence": float, "box_xyxy": [x1,y1,x2,y2]}.
    """
    if not detections:
        listing = "(no defects were detected)"
    else:
        listing = "\n".join(
            f"- {d['class_name']} (confidence {d['confidence']:.2f}) at {d['box_xyxy']}"
            for d in detections
        )
    return PROMPT_TEMPLATE.format(detections=listing)


def generate_report(
    image_path: Path,
    detections: list[dict],
    client: anthropic.Anthropic | None = None,
) -> str:
    """Generate a markdown inspection report for an image and its detections."""
    if client is None:
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env/.env

    media_type = MEDIA_TYPES[image_path.suffix.lower()]
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": build_prompt(detections)},
                ],
            }
        ],
    )

    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude refused to generate a report for {image_path.name}")

    return "".join(block.text for block in response.content if block.type == "text")
