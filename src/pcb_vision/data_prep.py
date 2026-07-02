"""Convert the PKU-Market-PCB dataset (Pascal VOC XML) to YOLO format.

Reads  data/raw/PCB_DATASET/{images,Annotations}/<Class>/...
Writes data/processed/pcb_yolo/{images,labels}/{train,val,test}/ + dataset.yaml

Split is 80/10/10, stratified per defect class, seeded for reproducibility.
Images are downscaled to a max side of 1600px (labels are normalized, so
coordinates are unaffected) to keep the Colab upload zip small.
"""

from __future__ import annotations

import argparse
import random
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import yaml
from PIL import Image

# Canonical class order — index in this list is the YOLO class id.
CLASSES = [
    "missing_hole",
    "mouse_bite",
    "open_circuit",
    "short",
    "spur",
    "spurious_copper",
]

SPLITS = {"train": 0.8, "val": 0.1, "test": 0.1}
MAX_SIDE = 1600
JPEG_QUALITY = 90


def voc_box_to_yolo(
    box: tuple[int, int, int, int], img_w: int, img_h: int
) -> tuple[float, float, float, float]:
    """Convert a VOC (xmin, ymin, xmax, ymax) box to normalized YOLO (cx, cy, w, h)."""
    xmin, ymin, xmax, ymax = box
    cx = (xmin + xmax) / 2.0 / img_w
    cy = (ymin + ymax) / 2.0 / img_h
    w = (xmax - xmin) / img_w
    h = (ymax - ymin) / img_h
    return cx, cy, w, h


def parse_voc_xml(path: Path) -> tuple[str, int, int, list[tuple[str, tuple]]]:
    """Parse a VOC annotation file.

    Returns (filename, width, height, objects) where objects is a list of
    (class_name, (xmin, ymin, xmax, ymax)).
    """
    root = ET.parse(path).getroot()
    filename = root.findtext("filename")
    width = int(root.findtext("size/width"))
    height = int(root.findtext("size/height"))
    objects = []
    for obj in root.iter("object"):
        name = obj.findtext("name").strip().lower()
        bb = obj.find("bndbox")
        box = tuple(int(float(bb.findtext(k))) for k in ("xmin", "ymin", "xmax", "ymax"))
        objects.append((name, box))
    return filename, width, height, objects


def _assign_splits(items: list, seed: int) -> dict[str, list]:
    """Shuffle items deterministically and split 80/10/10."""
    items = sorted(items)  # stable base order before seeded shuffle
    rng = random.Random(seed)
    rng.shuffle(items)
    n = len(items)
    n_train = round(n * SPLITS["train"])
    n_val = round(n * SPLITS["val"])
    return {
        "train": items[:n_train],
        "val": items[n_train : n_train + n_val],
        "test": items[n_train + n_val :],
    }


def prepare_dataset(raw_dir: Path, out_dir: Path, seed: int = 42) -> dict:
    """Convert the raw VOC dataset into a YOLO-format directory.

    Returns a summary dict: {"images": {split: count}, "boxes": {class: count}}.
    """
    ann_root = raw_dir / "Annotations"
    img_root = raw_dir / "images"
    if not ann_root.is_dir():
        raise FileNotFoundError(f"Annotations dir not found: {ann_root}")

    for split in SPLITS:
        (out_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    image_counts: dict[str, int] = defaultdict(int)
    box_counts: dict[str, int] = defaultdict(int)

    for class_dir in sorted(ann_root.iterdir()):
        if not class_dir.is_dir():
            continue
        xml_files = sorted(class_dir.glob("*.xml"))
        for split, files in _assign_splits(xml_files, seed).items():
            for xml_path in files:
                filename, _, _, objects = parse_voc_xml(xml_path)
                src_img = img_root / class_dir.name / filename
                if not src_img.exists():
                    raise FileNotFoundError(f"Image missing for {xml_path}: {src_img}")

                # Normalize against the *actual* image size (robust to stale XML dims),
                # downscale, and save.
                with Image.open(src_img) as im:
                    img_w, img_h = im.size
                    lines = []
                    for name, box in objects:
                        if name not in CLASSES:
                            raise ValueError(f"Unknown class {name!r} in {xml_path}")
                        cx, cy, w, h = voc_box_to_yolo(box, img_w, img_h)
                        cls_id = CLASSES.index(name)
                        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
                        box_counts[name] += 1

                    if max(im.size) > MAX_SIDE:
                        scale = MAX_SIDE / max(im.size)
                        im = im.resize(
                            (round(img_w * scale), round(img_h * scale)), Image.LANCZOS
                        )
                    im.convert("RGB").save(
                        out_dir / "images" / split / f"{xml_path.stem}.jpg",
                        quality=JPEG_QUALITY,
                    )

                label_path = out_dir / "labels" / split / f"{xml_path.stem}.txt"
                label_path.write_text("\n".join(lines) + "\n")
                image_counts[split] += 1

    dataset_yaml = {
        "path": str(out_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": dict(enumerate(CLASSES)),
    }
    (out_dir / "dataset.yaml").write_text(yaml.safe_dump(dataset_yaml, sort_keys=False))

    return {"images": dict(image_counts), "boxes": dict(box_counts)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/PCB_DATASET"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed/pcb_yolo"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    summary = prepare_dataset(args.raw_dir, args.out_dir, args.seed)
    print(f"Dataset written to {args.out_dir}")
    print(f"Images per split: {summary['images']}")
    print(f"Boxes per class:  {summary['boxes']}")


if __name__ == "__main__":
    main()
