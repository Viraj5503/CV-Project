# PCB Defect Detection (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A resume-grade computer-vision project: fine-tuned YOLOv11 that detects 6 PCB defect classes, with AI-written inspection reports, served via FastAPI + Streamlit + Docker.

**Architecture:** Offline pipeline converts the PKU-Market-PCB dataset (Pascal VOC XML) to YOLO format with a stratified 80/10/10 split; training happens in Google Colab (user runs the notebook, returns `best.pt`); local evaluation produces metrics/plots; a FastAPI service wraps inference + Claude-vision report generation; Streamlit is the demo UI.

**Tech Stack:** Python 3.11 (`.venv`), Ultralytics YOLOv11, PyTorch (mps locally / CUDA on Colab), Anthropic API (VLM reports), FastAPI, Streamlit, Docker, pytest.

## Global Constraints

- Python venv: `.venv` created from `/opt/homebrew/opt/python@3.11/bin/python3.11` (system 3.14 is too new for torch)
- Dataset: `data/raw/PCB_DATASET/` — 693 images, 6 classes, VOC XML in `Annotations/<Class>/`, images in `images/<Class>/`. NEVER commit `data/` (gitignored). Re-download: `git clone --depth 1 https://github.com/Ironbrotherstyle/PCB-DATASET.git` (mirror of PKU-Market-PCB; official source is Baidu-only). The mirror's `rotation/` set has no bbox labels — excluded by design (online augmentation replaces it)
- Class names (canonical order, index = YOLO class id): `missing_hole, mouse_bite, open_circuit, short, spur, spurious_copper`
- Split: 80/10/10 train/val/test, stratified per class, `random.seed(42)`
- Training: `yolo11s.pt` base, `imgsz=1024` (defects are ~40px on ~3000px images), Colab T4
- Secrets: `ANTHROPIC_API_KEY` from env / `.env` (gitignored); never hardcode
- User effort budget: ONLY the Colab run (~15 min). Everything else automated here
- Each task ends: run tests → verify → `git commit`
- GitHub username Viraj5503; `gh` CLI not installed (install or use git+PAT at Task 5)

---

### Task 1: Data prep — VOC→YOLO conversion, stratified split, EDA

**Files:**
- Create: `src/pcb_vision/__init__.py`, `src/pcb_vision/data_prep.py`, `src/pcb_vision/eda.py`
- Test: `tests/test_data_prep.py`
- Output (gitignored): `data/processed/pcb_yolo/{images,labels}/{train,val,test}/`, `data/processed/pcb_yolo/dataset.yaml`
- Output (committed): `reports/dataset_stats.md`, `reports/figures/class_distribution.png`, `reports/figures/sample_annotations.png`

**Interfaces:**
- Produces: `voc_box_to_yolo(box: tuple[int,int,int,int], img_w: int, img_h: int) -> tuple[float,float,float,float]` (xmin,ymin,xmax,ymax → normalized cx,cy,w,h); `parse_voc_xml(path: Path) -> tuple[str, int, int, list[tuple[str, tuple]]]` (filename, w, h, [(class, box)]); `prepare_dataset(raw_dir: Path, out_dir: Path, seed: int = 42) -> dict` (returns split counts); CLI: `python -m pcb_vision.data_prep`
- `dataset.yaml` keys: `path` (absolute), `train/val/test` (relative image dirs), `names` (id→name dict in canonical order)

Steps: write failing tests for `voc_box_to_yolo` + `parse_voc_xml` → implement → run `prepare_dataset` → EDA stats/figures → commit.

### Task 2: Colab training notebook

**Files:**
- Create: `notebooks/train_colab.ipynb`, `scripts/make_dataset_zip.py` (zips `data/processed/pcb_yolo` → `data/pcb_yolo.zip` for upload)

**Interfaces:**
- Consumes: `data/processed/pcb_yolo/` from Task 1
- Produces: `models/best.pt` (user downloads `pcb_yolo11s_run.zip` from Colab containing `best.pt`, `results.csv`, `args.yaml`, curve PNGs; unzip into `models/`)

Notebook cells (self-contained, in order): (1) `!nvidia-smi` + `%pip install ultralytics`; (2) upload/unzip `pcb_yolo.zip` (`files.upload()` with Drive-mount fallback); (3) rewrite `dataset.yaml` `path:` to the Colab unzip location; (4) train: `YOLO("yolo11s.pt").train(data=..., epochs=120, imgsz=1024, batch=8, patience=25, seed=42, project="runs", name="pcb_yolo11s")`; (5) val on test split; (6) zip weights+metrics → `files.download()`. Every cell idempotent; user just presses Run-all.

### Task 3: Evaluation + VLM inspection reports

**Files:**
- Create: `src/pcb_vision/evaluate.py`, `src/pcb_vision/report.py`
- Test: `tests/test_report.py` (prompt construction + response parsing, mocked API)
- Output (committed): `reports/evaluation.md` (mAP50, mAP50-95, per-class P/R/mAP table), `reports/figures/confusion_matrix.png`, `reports/figures/predictions_gallery.png`

**Interfaces:**
- Consumes: `models/best.pt`
- Produces: `evaluate(weights: Path, data_yaml: Path, device: str = "mps") -> dict` (metrics dict); `generate_report(image_path: Path, detections: list[dict], client: anthropic.Anthropic | None = None) -> str` — detections item: `{"class_name": str, "confidence": float, "box_xyxy": [x1,y1,x2,y2]}`; report = structured markdown (summary, per-defect severity/location/likely cause, recommended action)
- CHECK the `claude-api` skill before writing `report.py` (model id + vision request shape); read `dataviz` skill before figures

### Task 4: FastAPI + Streamlit + Docker

**Files:**
- Create: `src/pcb_vision/api.py` (FastAPI), `app/streamlit_app.py`, `Dockerfile`, `docker-compose.yml`, `.env.example`
- Test: `tests/test_api.py` (TestClient: /health, /inspect with sample image, 422 on bad upload)

**Interfaces:**
- Consumes: `models/best.pt`, `generate_report()` from Task 3
- Produces: `GET /health` → `{"status":"ok","model_loaded":true}`; `POST /inspect?conf=0.25&with_report=false` (multipart image) → `{"detections":[{class_name,confidence,box_xyxy}], "annotated_image_b64": str, "report": str|null, "inference_ms": float}`
- Streamlit: upload → calls API (URL from `PCB_API_URL`, default `http://localhost:8000`) → original vs annotated side-by-side, confidence slider, detections table, report expander. Read `frontend-design` + `dataviz` skills first
- Docker: python:3.11-slim, installs requirements, copies `src/ app/ models/best.pt`, compose runs api (8000) + ui (8501)

### Task 5: README, polish, GitHub publish

**Files:**
- Create: `README.md` (hero image, badges, architecture diagram, metrics tables from Task 3, quickstart: clone → download dataset → prep → train-or-download-weights → run demo; Docker one-liner), `LICENSE` (MIT), `docs/resume_bullets.md` (3-4 quantified bullets using real metrics)
- Verify fresh-clone quickstart works; `git remote add origin git@github.com:Viraj5503/pcb-defect-detection.git` (or HTTPS+PAT); push; confirm rendering

### Phase 2 (post-exams): RAG add-on

Vector DB (chromadb) over self-authored IPC-A-610-*style* acceptability summaries (public standards are copyrighted — write our own knowledge base citing public sources); `defect class → retrieve standard excerpt → repair recommendation` appended to Task 3 reports; evaluation via retrieval hit-rate on held-out Q&A. Detailed plan written after Phase 1 ships.

## Status log

- 2026-07-02: Plan written. Task 1 in progress — dataset cloned to `data/raw/PCB_DATASET/` (693 imgs verified: 115-116/class), repo scaffolded, `.venv` (3.11.15) created.
- 2026-07-02: **Task 1 COMPLETE.** 6/6 tests pass. Converted 693 imgs → `data/processed/pcb_yolo/` (train 555 / val 72 / test 66; 2,953 boxes — matches published count exactly). Median defect ~45px → confirms `imgsz=1024`. EDA figures + `reports/dataset_stats.md` written and visually verified. Viraj commits each step himself (no Claude attribution). Next: Task 2 (Colab notebook + dataset zip script).
