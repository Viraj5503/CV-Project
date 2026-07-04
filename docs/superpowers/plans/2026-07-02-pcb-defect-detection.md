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
- 2026-07-02: **Task 2 COMPLETE.** `scripts/make_dataset_zip.py` + `notebooks/train_colab.ipynb` written. Zip built and verified: `data/pcb_yolo.zip` (1,387 members = 693 imgs + 693 labels + dataset.yaml; 260 MB; split counts match Task 1 exactly). Notebook: 6 idempotent code cells (JSON + per-cell syntax verified), upload with Drive fallback, skips training if `best.pt` exists. 6/6 tests still pass. **BLOCKED on Viraj:** run notebook in Colab (T4), unzip `pcb_yolo11s_run.zip` into `models/`. Then Task 3 (evaluation + VLM reports).
- 2026-07-02: **Colab run DONE (Viraj).** Early-stopped at epoch 88 (best = epoch 63): val mAP50 0.972, mAP50-95 0.551, P 0.983, R 0.962. Run folder at `models/pcb_yolo11s_run/`, weights copied to `models/best.pt`.
- 2026-07-03: **Task 4a (FastAPI half) COMPLETE.** `src/pcb_vision/api.py` built TDD (6 new tests, YOLO + report mocked): `GET /health`, `POST /inspect?conf&with_report` → detections + base64-JPEG annotated image + optional Claude report + inference_ms. Model lazy-loaded/cached (`PCB_MODEL_PATH`, `PCB_DEVICE` env-configurable), eager-load via lifespan, 422 on bad uploads. Fixed test fixture (hex PNG blob was corrupt — PIL rejects it; test_report.py unaffected since it never decodes). 19/19 tests pass. End-to-end verified with real weights on mps: 3/3 missing_hole detections match the live report run, 146ms. **Remaining Task 4b (next session): `app/streamlit_app.py` (read frontend-design + dataviz skills first), `Dockerfile`, `docker-compose.yml`; verify uvicorn + docker compose up.**
- 2026-07-03: **API setup DONE.** `.env` + `.env.example` created, `python-dotenv` added, `report.py` model now env-configurable (`PCB_VLM_MODEL`, default `claude-opus-4-8`; Viraj's key runs `claude-sonnet-4-6`). `scripts/check_api.py` smoke test passes (key valid, model reachable — free call). **Live end-to-end verified:** YOLO (mps) + Claude vision on `01_missing_hole_04.jpg` → 3 detections → `reports/sample_inspection_report.md` (severity/location/cause/rework all sensible). 13/13 tests pass. Task 4 unblocked.
- 2026-07-04: **Task 4b COMPLETE — Task 4 done.** Anthropic credits exhausted → new requirement handled first: `report_error` field via TDD (`/inspect?with_report=true` returns 200 + detections + clean message instead of 500; verified live against the real credit-exhausted API). `app/streamlit_app.py` + `.streamlit/config.toml`: PCB-material theme (solder-mask surface `#101913`, copper accent `#C87941`, silkscreen mono title block with live API-health LED), side-by-side source/detections, stat tiles, copper ProgressColumn table, report expander with no-credits warning; 2 test-split sample boards bundled in `app/samples/`. `Dockerfile` (python:3.11-slim, CPU torch wheels, 2.74GB shared image) + `docker-compose.yml` (ui gated on api healthcheck, optional `.env` — never baked into the image, see `.dockerignore`) + serving vars documented in `.env.example`. Verified: 20/20 tests; local uvicorn (148ms mps) + Streamlit UI visually confirmed (PDF export); `docker compose up`: api healthy, containerized detections match the mps run exactly (3× missing_hole 0.82/0.81/0.78, 880ms CPU), ui→api DNS ok, torn down clean. Next: Task 5 (README, LICENSE, resume bullets, GitHub publish).
- 2026-07-02: **Task 3 COMPLETE.** `report.py` (Claude vision reports, model `claude-opus-4-8`, base64 image + detections prompt, refusal handling) built TDD — 7 mocked tests; `evaluate.py` ran on mps: **test mAP50 0.9565, mAP50-95 0.5239** (weakest class: spur, R 0.776 — 9 missed in confusion matrix). Wrote `reports/evaluation.md` + `reports/figures/{confusion_matrix,predictions_gallery}.png` (gallery visually verified; fixed spur/spurious_copper filename-substring bug). `.gitignore`: added `data/*.zip` + `models/pcb_yolo11s_run/`. 13/13 tests pass. NOTE: no `.env`/`ANTHROPIC_API_KEY` yet — live report call unverified (mocked only); needed for Task 4 demo. Next: Task 4 (FastAPI + Streamlit + Docker).
