"""Evaluate the fine-tuned YOLOv11 detector on the held-out test split.

Runs Ultralytics val on the test split, writes reports/evaluation.md
(overall + per-class metrics), copies the confusion matrix figure, and
renders a predictions gallery (one annotated test image per defect class).

CLI: python -m pcb_vision.evaluate [--weights ...] [--data ...] [--device mps]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import yaml
from ultralytics import YOLO

from pcb_vision.data_prep import CLASSES

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS = REPO_ROOT / "models" / "best.pt"
DEFAULT_DATA = REPO_ROOT / "data" / "processed" / "pcb_yolo" / "dataset.yaml"
REPORTS_DIR = REPO_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

INK_SECONDARY = "#4a4a4a"  # neutral ink for labels — never series color


def evaluate(weights: Path, data_yaml: Path, device: str = "mps") -> dict:
    """Run validation on the test split and return a metrics dict."""
    model = YOLO(str(weights))
    results = model.val(
        data=str(data_yaml), split="test", imgsz=1024, device=device, plots=True
    )
    per_class = {}
    for idx, class_id in enumerate(results.box.ap_class_index):
        precision, recall, ap50, ap = results.box.class_result(idx)
        per_class[results.names[int(class_id)]] = {
            "precision": float(precision),
            "recall": float(recall),
            "mAP50": float(ap50),
            "mAP50-95": float(ap),
        }
    return {
        "mAP50": float(results.box.map50),
        "mAP50-95": float(results.box.map),
        "precision": float(results.box.mp),
        "recall": float(results.box.mr),
        "per_class": per_class,
        "save_dir": Path(results.save_dir),
    }


def write_evaluation_md(metrics: dict, out_path: Path) -> None:
    """Write the evaluation report markdown from a metrics dict."""
    lines = [
        "# Model Evaluation — YOLOv11s on PKU-Market-PCB",
        "",
        "Held-out **test split** (66 images), `imgsz=1024`, weights `models/best.pt`",
        "(fine-tuned from `yolo11s.pt` on Colab T4, 88 epochs, early-stopped, seed 42).",
        "",
        "## Overall",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| mAP50 | {metrics['mAP50']:.4f} |",
        f"| mAP50-95 | {metrics['mAP50-95']:.4f} |",
        f"| Precision | {metrics['precision']:.4f} |",
        f"| Recall | {metrics['recall']:.4f} |",
        "",
        "## Per class",
        "",
        "| Class | Precision | Recall | mAP50 | mAP50-95 |",
        "|---|---|---|---|---|",
    ]
    for name, m in metrics["per_class"].items():
        lines.append(
            f"| {name} | {m['precision']:.4f} | {m['recall']:.4f} "
            f"| {m['mAP50']:.4f} | {m['mAP50-95']:.4f} |"
        )
    lines += [
        "",
        "## Figures",
        "",
        "![Confusion matrix](figures/confusion_matrix.png)",
        "",
        "![Predictions gallery](figures/predictions_gallery.png)",
        "",
    ]
    out_path.write_text("\n".join(lines))


def make_predictions_gallery(
    weights: Path, data_yaml: Path, out_path: Path, device: str = "mps"
) -> list[Path]:
    """Render a 2x3 grid: one annotated test prediction per defect class."""
    cfg = yaml.safe_load(data_yaml.read_text())
    test_dir = Path(cfg["path"]) / cfg["test"]
    # Filenames are "NN_<class>_NN.jpg"; match "_<class>_" so "spur" does not
    # also match "spurious_copper" files.
    images = []
    for cls in CLASSES:
        match = sorted(p for p in test_dir.iterdir() if f"_{cls}_" in p.name)
        if match:
            images.append((cls, match[0]))

    model = YOLO(str(weights))
    results = model.predict(
        [str(p) for _, p in images], imgsz=1024, conf=0.25, device=device
    )

    fig, axes = plt.subplots(2, 3, figsize=(15, 7))
    for ax, (cls, _), result in zip(axes.flat, images, results):
        ax.imshow(result.plot()[:, :, ::-1])  # BGR -> RGB
        ax.set_title(f"{cls} — {len(result.boxes)} detected", fontsize=10, color=INK_SECONDARY)
        ax.axis("off")
    for ax in axes.flat[len(images):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [p for _, p in images]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    metrics = evaluate(args.weights, args.data, device=args.device)
    write_evaluation_md(metrics, REPORTS_DIR / "evaluation.md")
    shutil.copy(metrics["save_dir"] / "confusion_matrix.png", FIGURES_DIR / "confusion_matrix.png")
    make_predictions_gallery(
        args.weights, args.data, FIGURES_DIR / "predictions_gallery.png", device=args.device
    )

    print(f"test mAP50: {metrics['mAP50']:.4f}  mAP50-95: {metrics['mAP50-95']:.4f}")
    print(f"wrote {REPORTS_DIR / 'evaluation.md'} + figures")


if __name__ == "__main__":
    main()
