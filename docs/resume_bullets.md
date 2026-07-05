# Resume bullets — PCB Defect Detection

Project: **PCB Defect Detection** — https://github.com/Viraj5503/PCB-Defect-Detection

All numbers below are real, reproducible from `reports/evaluation.md` and the
test suite in this repo.

## Bullets (pick 3–4)

- Fine-tuned **YOLOv11s** (1024 px input) on the PKU-Market-PCB dataset (693 images,
  6 defect classes) to **0.957 mAP@50 / 0.95 precision / 0.93 recall** on a held-out
  test split, running at **~148 ms/image** on Apple-silicon (MPS).
- Built an end-to-end inspection service around the model: **FastAPI** inference API +
  **Streamlit** review UI, shipped as a two-service **Docker Compose** stack
  (CPU-only PyTorch image, health-check-gated startup) whose containerized detections
  match the native MPS run exactly.
- Integrated **Claude vision** to turn raw detections into structured inspection
  reports (severity, location, likely root cause, recommended rework), with graceful
  degradation so detection stays fully available when the LLM API is unreachable or
  out of credits.
- Engineered a reproducible data pipeline (**Pascal VOC → YOLO** conversion,
  stratified 80/10/10 split over **2,953 annotated defects**, pinned seeds) and a
  **20-test pytest suite** written test-first covering conversion, the API, and
  report generation.

## Shorter variants (space-constrained resume)

- Fine-tuned YOLOv11s to 0.957 mAP@50 across 6 PCB defect classes; ~148 ms/image on
  Apple-silicon.
- Served the model via FastAPI + Streamlit in a health-checked Docker Compose stack.
- Added Claude-vision inspection reports with graceful degradation when the API is
  unavailable.

## Interview talking points

- **Why 1024 px input:** median defect is ~45 px on ~3000 px source images; at the
  default 640 px training size defects shrink below reliable detection size.
- **Weakest class and why:** `spur` (recall 0.78) — visually similar to
  `spurious_copper`; confusion matrix in `reports/figures/confusion_matrix.png`.
- **Production thinking:** the LLM report is an optional enrichment, never a
  dependency — `/inspect` returns HTTP 200 with detections plus a `report_error`
  field instead of failing when report generation breaks.
- **NXP tie-in:** automated optical inspection of PCBs is a real manufacturing QA
  problem; this mirrors the detect → classify → document workflow of an AOI station.
