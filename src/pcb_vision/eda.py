"""Dataset EDA — class distribution figure, annotated samples grid, stats report.

Reads the processed YOLO dataset and writes README-ready PNGs + a stats markdown.
Colors follow the project viz tokens (light surface, single-hue series).
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

from pcb_vision.data_prep import CLASSES

# Viz tokens (light mode) — validated reference palette
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SERIES = "#2a78d6"  # categorical slot 1 (blue)
BOX_COLOR = "#e34948"  # red — pops against green PCB imagery

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "text.color": INK,
        "axes.edgecolor": BASELINE,
        "axes.labelcolor": INK_2,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
    }
)


def collect_stats(dataset_dir: Path) -> dict:
    """Walk labels + images and aggregate per-class/per-split statistics."""
    stats = {
        "images_per_split": {},
        "boxes_per_class": defaultdict(int),
        "box_rel_areas": [],  # normalized box area (w*h), all splits
        "box_px_sides": [],  # longest box side in pixels (processed images)
    }
    for split in ("train", "val", "test"):
        label_dir = dataset_dir / "labels" / split
        img_dir = dataset_dir / "images" / split
        labels = sorted(label_dir.glob("*.txt"))
        stats["images_per_split"][split] = len(labels)
        for lp in labels:
            with Image.open(img_dir / f"{lp.stem}.jpg") as im:
                img_w, img_h = im.size
            for line in lp.read_text().splitlines():
                cls_id, _, _, w, h = line.split()
                w, h = float(w), float(h)
                stats["boxes_per_class"][CLASSES[int(cls_id)]] += 1
                stats["box_rel_areas"].append(w * h)
                stats["box_px_sides"].append(max(w * img_w, h * img_h))
    return stats


def plot_class_distribution(stats: dict, out_path: Path) -> None:
    """Bar chart of boxes per class + histogram of defect sizes."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))

    counts = [stats["boxes_per_class"][c] for c in CLASSES]
    labels = [c.replace("_", " ") for c in CLASSES]
    bars = ax1.bar(labels, counts, color=SERIES, width=0.62)
    ax1.bar_label(bars, padding=3, color=INK_2, fontsize=9)
    ax1.set_title("Annotated defects per class", color=INK, loc="left", fontsize=11)
    ax1.tick_params(axis="x", rotation=20)

    ax2.hist(stats["box_px_sides"], bins=40, color=SERIES)
    ax2.set_title(
        "Defect size — longest box side (px)", color=INK, loc="left", fontsize=11
    )
    ax2.set_xlabel("pixels (on 1600px-max images)")

    for ax in (ax1, ax2):
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_sample_annotations(dataset_dir: Path, out_path: Path) -> None:
    """2x3 grid: one training sample per class with its boxes drawn."""
    img_dir = dataset_dir / "images" / "train"
    label_dir = dataset_dir / "labels" / "train"

    fig, axes = plt.subplots(2, 3, figsize=(13, 5.4))
    for ax, cls in zip(axes.flat, CLASSES):
        cls_id = CLASSES.index(cls)
        # first train image whose label file contains this class
        sample = next(
            lp
            for lp in sorted(label_dir.glob("*.txt"))
            if any(line.split()[0] == str(cls_id) for line in lp.read_text().splitlines())
        )
        with Image.open(img_dir / f"{sample.stem}.jpg") as im:
            img_w, img_h = im.size
            ax.imshow(im)
        for line in sample.read_text().splitlines():
            cx, cy, w, h = (float(v) for v in line.split()[1:5])
            bw, bh = w * img_w, h * img_h
            x0, y0 = cx * img_w - bw / 2, cy * img_h - bh / 2
            ax.add_patch(
                Rectangle((x0, y0), bw, bh, fill=False, edgecolor=BOX_COLOR, linewidth=1.6)
            )
        ax.set_title(cls.replace("_", " "), color=INK, fontsize=10, loc="left")
        ax.axis("off")
    fig.suptitle("Sample annotations (train split)", color=INK, x=0.065, ha="left")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def write_stats_md(stats: dict, out_path: Path) -> None:
    areas = sorted(stats["box_rel_areas"])
    sides = sorted(stats["box_px_sides"])
    median_side = sides[len(sides) // 2]
    median_area_pct = areas[len(areas) // 2] * 100
    total_imgs = sum(stats["images_per_split"].values())
    total_boxes = sum(stats["boxes_per_class"].values())

    lines = [
        "# Dataset statistics — PKU-Market-PCB (processed)",
        "",
        f"- **Images:** {total_imgs} (train {stats['images_per_split']['train']} / "
        f"val {stats['images_per_split']['val']} / test {stats['images_per_split']['test']}, "
        "stratified 80/10/10, seed 42)",
        f"- **Annotated defects:** {total_boxes}",
        f"- **Median defect size:** {median_side:.0f}px longest side "
        f"({median_area_pct:.3f}% of image area) — small-object regime, "
        "motivating training at `imgsz=1024`",
        "- Images downscaled to max side 1600px (labels are normalized; unaffected)",
        "- The mirror's `rotation/` split ships without bounding boxes and is excluded; "
        "online augmentation (mosaic, flips, HSV) covers rotation invariance during training",
        "",
        "| Class | Boxes |",
        "|---|---|",
    ]
    lines += [f"| {c} | {stats['boxes_per_class'][c]} |" for c in CLASSES]
    lines += [
        "",
        "![Class distribution](figures/class_distribution.png)",
        "",
        "![Sample annotations](figures/sample_annotations.png)",
        "",
    ]
    out_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-dir", type=Path, default=Path("data/processed/pcb_yolo")
    )
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()

    figures_dir = args.reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    stats = collect_stats(args.dataset_dir)
    plot_class_distribution(stats, figures_dir / "class_distribution.png")
    plot_sample_annotations(args.dataset_dir, figures_dir / "sample_annotations.png")
    write_stats_md(stats, args.reports_dir / "dataset_stats.md")
    print(f"Wrote stats + figures to {args.reports_dir}/")


if __name__ == "__main__":
    main()
