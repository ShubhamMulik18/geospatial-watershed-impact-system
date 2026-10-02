"""Prepare one photograph for the watershed MobileNetV2 baseline.

Save this file as ai/inference/preprocess.py in your project.
From the project root, run:
    .venv-ai/bin/python ai/inference/preprocess.py path/to/photo.jpg

Public functions:
    load_rgb_image(path): an independent, orientation-corrected RGB PIL image.
    preprocess_image(path): one CPU float32 tensor with shape (3, 224, 224).

Validation, testing and prediction must use the same deterministic processing:
EXIF orientation -> RGB -> resize shorter edge to 232 -> centre crop to 224
-> scale to [0, 1] -> ImageNet normalisation. The final normalised tensor is
not restricted to [0, 1]. Transparent pixels are composited over white.

The transform is the official MobileNet_V2_Weights.IMAGENET1K_V2 preset,
with bilinear interpolation and antialiasing enabled. No model or weights
are loaded or downloaded. Source files are only read, never changed.

Training can reuse load_rgb_image before its own random augmentation.
The future predictor will add a batch dimension and choose the compute device.
The backend must supply a trusted local path; this module does not accept URLs
or resolve user-uploaded file identifiers.

Reference:
https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v2.html
"""

from __future__ import annotations

import argparse
import sys
import warnings
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageOps, UnidentifiedImageError

if TYPE_CHECKING:
    from torch import Tensor


def load_rgb_image(image_path: str | Path) -> Image.Image:
    """Decode one photograph and return an RGB copy with EXIF orientation applied.

    Raises ValueError for missing, unreadable, oversized or multi-frame input.
    Pillow's decompression-bomb warning is treated as an error. Do not disable
    Pillow's image-size safeguards or enable loading truncated images globally.
    The returned image owns its pixels and remains usable after the file closes.
    """
    path = Path(image_path)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            # Check the container, then reopen to decode the actual pixels.
            with Image.open(path) as source:
                if getattr(source, "n_frames", 1) != 1:
                    raise ValueError(
                        f"{path}: Use a single photograph, not a multi-frame image."
                    )
                source.verify()

            with Image.open(path) as source:
                source.load()
                oriented = ImageOps.exif_transpose(source)
                if "A" in oriented.getbands() or "transparency" in oriented.info:
                    rgba = oriented.convert("RGBA")
                    background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                    return Image.alpha_composite(background, rgba).convert("RGB")
                return oriented.convert("RGB")
    except FileNotFoundError as exc:
        raise ValueError(f"Image file not found: {path}") from exc
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValueError(f"Cannot safely read image {path}: {exc}") from exc


@lru_cache(maxsize=1)
def _evaluation_transform():
    """Create the fixed torchvision transform only when preprocessing is used."""
    from torchvision.models import MobileNet_V2_Weights

    # Calling transforms() does not construct a model or download its weights.
    return MobileNet_V2_Weights.IMAGENET1K_V2.transforms(antialias=True)


def preprocess_image(image_path: str | Path) -> Tensor:
    """Return one unbatched, normalised CPU tensor; do not save a resized photo."""
    with load_rgb_image(image_path) as image:
        return _evaluation_transform()(image)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check deterministic MobileNetV2 image preprocessing."
    )
    parser.add_argument("images", nargs="+", type=Path, help="Local photograph paths")
    args = parser.parse_args(argv)

    try:
        _evaluation_transform()
    except (ImportError, RuntimeError, OSError) as exc:
        print(f"ERROR: PyTorch/torchvision could not be loaded: {exc}", file=sys.stderr)
        print("Run this script with your project's .venv-ai/bin/python.", file=sys.stderr)
        return 2

    passed = 0
    for path in args.images:
        try:
            tensor = preprocess_image(path)
        except (ValueError, OSError) as exc:
            print(f"FAIL: {exc}")
            continue
        print(
            f"PASS: {path.name} | shape={tuple(tensor.shape)} "
            f"| dtype={tensor.dtype} | device={tensor.device}"
        )
        passed += 1

    print(f"\nPreprocessing passed for {passed}/{len(args.images)} image(s).")
    print("Source photographs were not changed. This is not a model prediction.")
    return 0 if passed == len(args.images) else 1


if __name__ == "__main__":
    raise SystemExit(main())
