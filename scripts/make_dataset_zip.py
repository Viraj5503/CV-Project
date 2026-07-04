"""Zip the processed YOLO dataset for upload to Google Colab.

Reads  data/processed/pcb_yolo/  (produced by `python -m pcb_vision.data_prep`)
Writes data/pcb_yolo.zip  with `pcb_yolo/` as the archive root, so unzipping
in Colab's /content yields /content/pcb_yolo/{dataset.yaml,images,labels}.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = REPO_ROOT / "data" / "processed" / "pcb_yolo"
DEFAULT_OUT = REPO_ROOT / "data" / "pcb_yolo.zip"


def make_zip(src_dir: Path, out_path: Path) -> int:
    """Archive src_dir into out_path (rooted at src_dir.name). Returns file count."""
    if not (src_dir / "dataset.yaml").is_file():
        raise FileNotFoundError(
            f"{src_dir} has no dataset.yaml — run `python -m pcb_vision.data_prep` first"
        )
    files = sorted(p for p in src_dir.rglob("*") if p.is_file())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, Path(src_dir.name) / path.relative_to(src_dir))
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    count = make_zip(args.src, args.out)
    size_mb = args.out.stat().st_size / 1024**2
    print(f"Wrote {args.out} ({count} files, {size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
