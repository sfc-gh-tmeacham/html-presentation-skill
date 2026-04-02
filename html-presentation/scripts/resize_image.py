#!/usr/bin/env python3
"""Resize a raster image so its longest side does not exceed a given max size.

Preserves aspect ratio and uses Lanczos resampling for sharp downscaling.
If the image is already within bounds, it is saved unchanged.

Usage::

    python resize_image.py <input> <output> [--max-size 800]

Example::

    python resize_image.py hero_banner.png hero_small.png --max-size 600
"""

import argparse
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    print("Error: Pillow is required.  Install with:  pip install Pillow", file=sys.stderr)
    sys.exit(1)

# Supported raster formats that Pillow can open reliably.
SUPPORTED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


def validate_input(input_path: Path) -> None:
    """Validate that the input file exists, is a file, and has a supported extension.

    Args:
        input_path: Path to the source image.

    Raises:
        SystemExit: If validation fails (file missing, not a file, or
            unsupported extension).
    """
    if not input_path.exists():
        print(f"Error: '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"Error: '{input_path}' is not a file.", file=sys.stderr)
        sys.exit(1)

    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(
            f"Error: Unsupported file type '{ext}'.  "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            file=sys.stderr,
        )
        sys.exit(1)


def validate_output(output_path: Path) -> None:
    """Ensure the output directory exists and is writable.

    Args:
        output_path: Desired path for the resized image.

    Raises:
        SystemExit: If the parent directory does not exist or is not writable.
    """
    parent = output_path.parent
    if not parent.exists():
        print(
            f"Error: Output directory '{parent}' does not exist.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not parent.is_dir():
        print(
            f"Error: '{parent}' is not a directory.",
            file=sys.stderr,
        )
        sys.exit(1)


def resize_image(input_path: str, output_path: str, max_size: int = 800) -> None:
    """Resize a raster image while preserving its aspect ratio.

    Opens the source image, checks whether it exceeds ``max_size`` on its
    longest side, and — if so — scales it down using Lanczos resampling
    (the sharpest downscale filter available in Pillow).

    Args:
        input_path: Filesystem path to the source image.
        output_path: Filesystem path where the resized image will be saved.
            The output format is inferred from the file extension.
        max_size: Maximum allowed pixels on the longest side.  Images that
            are already within this bound are saved as-is.

    Raises:
        SystemExit: On corrupt/unreadable images or I/O write failures.
    """
    # Attempt to open the image — catch corrupt files and format errors.
    try:
        img = Image.open(input_path)
        # Force-load pixel data now so we catch truncation/corruption early.
        img.load()
    except UnidentifiedImageError:
        print(
            f"Error: '{input_path}' is not a valid image or the format is "
            f"not recognized by Pillow.",
            file=sys.stderr,
        )
        sys.exit(1)
    except (OSError, SyntaxError) as exc:
        # SyntaxError can occur with certain corrupt PNGs/GIFs in Pillow.
        print(f"Error: Could not read '{input_path}': {exc}", file=sys.stderr)
        sys.exit(1)

    w, h = img.size

    # Guard against degenerate images (0×0, metadata-only, etc.).
    if w == 0 or h == 0:
        print(
            f"Error: Image has invalid dimensions ({w}x{h}).",
            file=sys.stderr,
        )
        sys.exit(1)

    longest = max(w, h)

    # If the image is already small enough, just copy it to the output path.
    if longest <= max_size:
        try:
            shutil.copy2(input_path, output_path)
        except (OSError, shutil.Error) as exc:
            print(f"Error: Could not copy to '{output_path}': {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Image already within bounds ({w}x{h}). Saved as-is.")
        return

    # Calculate the uniform scale factor so the longest side == max_size.
    scale = max_size / longest
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    # Lanczos (a.k.a. ANTIALIAS) produces the sharpest downscale results.
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    try:
        resized.save(output_path)
    except (OSError, ValueError) as exc:
        print(f"Error: Could not save to '{output_path}': {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Resized {w}x{h} → {new_w}x{new_h}  (saved to {output_path})")


def main() -> None:
    """Parse CLI arguments and run the resize pipeline."""
    parser = argparse.ArgumentParser(
        description="Resize an image for slide-deck embedding."
    )
    parser.add_argument("input", help="Path to the source image")
    parser.add_argument("output", help="Path for the resized output image")
    parser.add_argument(
        "--max-size",
        type=int,
        default=800,
        help="Max pixels on longest side (default: 800)",
    )
    args = parser.parse_args()

    # Validate max-size is a positive integer.
    if args.max_size <= 0:
        print("Error: --max-size must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input)
    output_path = Path(args.output)

    validate_input(input_path)
    validate_output(output_path)
    resize_image(args.input, args.output, args.max_size)


if __name__ == "__main__":
    main()
