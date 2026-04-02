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
import os
import shutil
import sys
import tempfile
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
    try:
        with Image.open(input_path) as img:
            img.load()
            w, h = img.size
            if w == 0 or h == 0:
                print(
                    f"Error: Image has invalid dimensions ({w}x{h}).",
                    file=sys.stderr,
                )
                sys.exit(1)

            longest = max(w, h)

            if longest <= max_size:
                tmp_fd, tmp_path_str = None, None
                try:
                    tmp_fd, tmp_path_str = tempfile.mkstemp(
                        dir=Path(output_path).parent,
                        suffix=Path(output_path).suffix,
                    )
                    os.close(tmp_fd)
                    tmp_fd = None
                    shutil.copy2(input_path, tmp_path_str)
                    os.replace(tmp_path_str, output_path)
                    tmp_path_str = None
                except (OSError, shutil.Error) as exc:
                    if tmp_fd is not None:
                        try:
                            os.close(tmp_fd)
                        except OSError:
                            pass
                    if tmp_path_str is not None:
                        try:
                            os.unlink(tmp_path_str)
                        except OSError:
                            pass
                    print(f"Error: Could not copy to '{output_path}': {exc}", file=sys.stderr)
                    sys.exit(1)
                print(f"Image already within bounds ({w}x{h}). Saved as-is.")
                return

            scale = max_size / longest
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            resized = img.resize((new_w, new_h), Image.LANCZOS)
    except UnidentifiedImageError:
        print(
            f"Error: '{input_path}' is not a valid image or the format is "
            f"not recognized by Pillow.",
            file=sys.stderr,
        )
        sys.exit(1)
    except (OSError, SyntaxError) as exc:
        print(f"Error: Could not read '{input_path}': {exc}", file=sys.stderr)
        sys.exit(1)

    tmp_fd2, tmp_path2 = None, None
    try:
        tmp_fd2, tmp_path2 = tempfile.mkstemp(
            dir=Path(output_path).parent,
            suffix=Path(output_path).suffix,
        )
        os.close(tmp_fd2)
        tmp_fd2 = None
        resized.save(tmp_path2)
        os.replace(tmp_path2, output_path)
        tmp_path2 = None
    except (OSError, ValueError) as exc:
        if tmp_fd2 is not None:
            try:
                os.close(tmp_fd2)
            except OSError:
                pass
        if tmp_path2 is not None:
            try:
                os.unlink(tmp_path2)
            except OSError:
                pass
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
