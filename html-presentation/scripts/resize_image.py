#!/usr/bin/env python3
"""Resize a raster image so its longest side does not exceed a given max size.

Preserves aspect ratio and uses Lanczos resampling for sharp downscaling.
If the image is already within bounds, it is saved unchanged.

Usage::

    python resize_image.py <input> <output> [--max-size 800]

Example::

    python resize_image.py hero_banner.png hero_small.png --max-size 600
"""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    print("Error: Pillow is required.  Install with:  pip install Pillow", file=sys.stderr)
    sys.exit(1)

# Supported raster formats that Pillow can open reliably.
SUPPORTED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

# Output formats that support EXIF and ICC profile metadata.
OUTPUT_EXIF_FORMATS: set[str] = {".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".png"}
OUTPUT_ICC_FORMATS: set[str] = {".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".png"}


def validate_input(input_path: Path) -> None:
    """Validate that the input file exists, is a file, and has a supported extension.

    Args:
        input_path: Path to the source image.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file or has an unsupported extension.
    """
    if not input_path.exists():
        print(f"Error: '{input_path}' not found.", file=sys.stderr)
        raise FileNotFoundError(f"'{input_path}' not found.")

    if not input_path.is_file():
        print(f"Error: '{input_path}' is not a file.", file=sys.stderr)
        raise ValueError(f"'{input_path}' is not a file.")

    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(
            f"Error: Unsupported file type '{ext}'.  "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            file=sys.stderr,
        )
        raise ValueError(f"Unsupported file type '{ext}'.")


def validate_output(output_path: Path) -> None:
    """Ensure the output directory exists and is writable.

    Args:
        output_path: Desired path for the resized image.

    Raises:
        FileNotFoundError: If the parent directory does not exist.
        ValueError: If the parent path is not a directory.
        OSError: If the parent directory is not writable.
    """
    parent = output_path.parent
    if not parent.exists():
        print(
            f"Error: Output directory '{parent}' does not exist.",
            file=sys.stderr,
        )
        raise FileNotFoundError(f"Output directory '{parent}' does not exist.")

    if not parent.is_dir():
        print(
            f"Error: '{parent}' is not a directory.",
            file=sys.stderr,
        )
        raise ValueError(f"'{parent}' is not a directory.")

    if not os.access(parent, os.W_OK):
        print(f"Error: Output directory '{parent}' is not writable.", file=sys.stderr)
        raise OSError(f"Output directory '{parent}' is not writable.")

    if output_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported output format '{output_path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )


@contextlib.contextmanager
def _atomic_write(output_path: str) -> Generator[str, None, None]:
    tmp_fd, tmp_path = None, None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=Path(output_path).parent,
            suffix=Path(output_path).suffix,
        )
        os.close(tmp_fd)
        tmp_fd = None
        yield tmp_path
        os.replace(tmp_path, output_path)
        tmp_path = None
    finally:
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def resize_image(input_path: Path, output_path: Path, max_size: int = 800) -> None:
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
        ValueError: If max_size is not positive, the image has invalid
            dimensions, or the image format is not recognized.
        OSError: On corrupt/unreadable images or I/O write failures.
    """
    if max_size <= 0:
        raise ValueError(f"max_size must be positive, got {max_size}")

    if input_path.resolve() == output_path.resolve():
        print("Warning: input and output paths are the same file.", file=sys.stderr)

    try:
        ctx = Image.open(input_path)
    except UnidentifiedImageError:
        print(
            f"Error: '{input_path}' is not a valid image or the format is "
            f"not recognized by Pillow.",
            file=sys.stderr,
        )
        raise ValueError(
            f"'{input_path}' is not a valid image or the format is not recognized by Pillow."
        )
    except (OSError, SyntaxError) as exc:
        print(f"Error: Could not read '{input_path}': {exc}", file=sys.stderr)
        raise OSError(f"Could not read '{input_path}': {exc}") from exc

    with ctx as img:
        try:
            img.load()
        except (OSError, SyntaxError) as exc:
            print(f"Error: Could not read '{input_path}': {exc}", file=sys.stderr)
            raise OSError(f"Could not read '{input_path}': {exc}") from exc

        if getattr(img, "n_frames", 1) > 1:
            print(
                f"Warning: '{input_path}' is an animated image; "
                "only the first frame will be used.",
                file=sys.stderr,
            )
        w, h = img.size
        if w == 0 or h == 0:
            print(
                f"Error: Image has invalid dimensions ({w}x{h}).",
                file=sys.stderr,
            )
            raise ValueError(f"Image has invalid dimensions ({w}x{h}).")

        longest = max(w, h)

        if longest <= max_size:
            try:
                with _atomic_write(str(output_path)) as tmp_path:
                    shutil.copy2(input_path, tmp_path)
            except (OSError, shutil.Error) as exc:
                print(f"Error: Could not copy to '{output_path}': {exc}", file=sys.stderr)
                raise OSError(f"Could not copy to '{output_path}': {exc}") from exc
            print(f"Image already within bounds ({w}x{h}). Saved as-is.")
            return

        scale = max_size / longest
        new_w = max(1, round(w * scale))
        new_h = max(1, round(h * scale))

        out_ext = output_path.suffix.lower()
        save_kwargs = {}
        if img.info.get("exif") and out_ext in OUTPUT_EXIF_FORMATS:
            save_kwargs["exif"] = img.info["exif"]
        if img.info.get("icc_profile") and out_ext in OUTPUT_ICC_FORMATS:
            save_kwargs["icc_profile"] = img.info["icc_profile"]

        try:
            with _atomic_write(str(output_path)) as tmp_path:
                with img.resize((new_w, new_h), Image.LANCZOS) as resized:
                    resized.save(tmp_path, **save_kwargs)
                    print(f"Resized {w}x{h} → {new_w}x{new_h}  (saved to {output_path})")
        except (OSError, ValueError) as exc:
            print(f"Error: Could not save to '{output_path}': {exc}", file=sys.stderr)
            raise OSError(f"Could not save to '{output_path}': {exc}") from exc


def positive_int(value: str) -> int:
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid integer.")
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"--max-size must be a positive integer, got {ivalue}.")
    return ivalue


def main() -> None:
    """Parse CLI arguments and run the resize pipeline."""
    parser = argparse.ArgumentParser(
        description="Resize an image for slide-deck embedding."
    )
    parser.add_argument("input", help="Path to the source image")
    parser.add_argument("output", help="Path for the resized output image")
    parser.add_argument(
        "--max-size",
        type=positive_int,
        default=800,
        help="Max pixels on longest side (default: 800)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        validate_input(input_path)
        validate_output(output_path)
        resize_image(input_path, output_path, args.max_size)
    except (FileNotFoundError, ValueError, OSError):
        sys.exit(1)


if __name__ == "__main__":
    main()
