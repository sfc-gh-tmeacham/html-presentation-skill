#!/usr/bin/env python3
"""Prepare a screenshot or photo for slide embedding in a single step.

Pipeline:
    1. Auto-crop uniform-color borders (white, black, or near-uniform).
    2. Resize so the longest side fits within ``--max-size``.
    3. Optionally add transparent padding around the result.
    4. Print the base64 data URI to stdout.

Diagnostics (original / cropped / final dimensions) are printed to stderr.

Usage::

    python screenshot_to_slide.py <input> [--max-size 800] [--padding 0]

Examples::

    python screenshot_to_slide.py ui_capture.png
    python screenshot_to_slide.py dashboard.png --max-size 600 --padding 16
"""

import argparse
import base64
import io
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageOps, UnidentifiedImageError
except ImportError:
    print(
        "Error: Pillow is required.  Install with:  pip install Pillow",
        file=sys.stderr,
    )
    sys.exit(1)

# Supported raster formats for screenshot processing.
SUPPORTED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


def validate_input(input_path: Path) -> None:
    """Validate that the input file exists, is a regular file, and has a supported extension.

    Args:
        input_path: Path to the source screenshot.

    Raises:
        SystemExit: If validation fails.
    """
    if not input_path.exists():
        print(f"Error: '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"Error: '{input_path}' is not a regular file.", file=sys.stderr)
        sys.exit(1)

    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(
            f"Error: Unsupported file type '{ext}'.  "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Warn on very large files — they'll produce huge data URIs.
    size_mb = input_path.stat().st_size / (1024 * 1024)
    if size_mb > 20:
        print(
            f"Warning: Input file is {size_mb:.1f} MB.  The resulting data URI "
            f"will be very large.  Consider pre-resizing with resize_image.py.",
            file=sys.stderr,
        )


def safe_open_image(input_path: Path) -> Image.Image:
    """Open and validate an image file, handling corrupt or unreadable files.

    Args:
        input_path: Path to the source image.

    Returns:
        A loaded PIL Image object.

    Raises:
        SystemExit: If the image cannot be opened, is corrupt, or has
            degenerate (0×0) dimensions.
    """
    try:
        img = Image.open(input_path)
        # Force-load pixel data now so truncation/corruption surfaces early.
        img.load()
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

    w, h = img.size
    if w == 0 or h == 0:
        print(f"Error: Image has invalid dimensions ({w}x{h}).", file=sys.stderr)
        sys.exit(1)

    return img


def auto_crop(img: Image.Image, fuzz: int = 15) -> Image.Image:
    """Remove uniform-color borders from an image.

    Compares every pixel to the top-left corner color.  Pixels that differ
    by less than ``fuzz`` (per-channel, 0-255) are treated as "border" and
    trimmed away.

    If cropping would remove the entire image (e.g. a solid-color image),
    the original is returned unchanged with a warning.

    Args:
        img: Source PIL Image.
        fuzz: Per-channel tolerance for border detection.  Higher values
            crop more aggressively (e.g. anti-aliased edges).

    Returns:
        A cropped copy of the image, or the original if no border was found
        or if cropping would produce an empty result.
    """
    try:
        # Convert to RGBA so we have a consistent 4-channel comparison.
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Build a solid image filled with the top-left pixel's color.
        bg = Image.new("RGBA", img.size, img.getpixel((0, 0)))

        # Compute per-pixel difference, convert to grayscale, then threshold.
        diff = ImageChops.difference(img, bg)
        diff = diff.convert("L")
        # Build a threshold lookup table once: values below fuzz map to 0
        # (border), values at or above map to 255 (content).
        lut = [0 if x < fuzz else 255 for x in range(256)]
        diff = diff.point(lut)

        # getbbox() returns the bounding box of all non-zero pixels.
        bbox = diff.getbbox()
        if bbox:
            cropped = img.crop(bbox)
            # Guard against degenerate crop results.
            if cropped.size[0] > 0 and cropped.size[1] > 0:
                return cropped
            print(
                "Warning: Crop produced a degenerate result.  "
                "Returning original image.",
                file=sys.stderr,
            )
            return img

        # No bounding box → the entire image is uniform color.
        print(
            "Warning: Image appears to be a single solid color.  "
            "Skipping crop.",
            file=sys.stderr,
        )
        return img
    except Exception as exc:
        # If anything unexpected happens during crop, recover gracefully.
        print(
            f"Warning: Auto-crop failed ({exc}).  Returning original image.",
            file=sys.stderr,
        )
        return img


def resize(img: Image.Image, max_size: int) -> Image.Image:
    """Scale an image down so its longest side does not exceed ``max_size``.

    Uses Lanczos resampling for sharp results.  Images already within
    bounds are returned unchanged.

    Args:
        img: Source PIL Image.
        max_size: Maximum allowed pixels on the longest side.

    Returns:
        A (possibly resized) copy of the image.
    """
    w, h = img.size
    longest = max(w, h)
    if longest <= max_size:
        return img

    # Uniform scale so the longest side lands exactly on max_size.
    scale = max_size / longest
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    try:
        return img.resize((new_w, new_h), Image.LANCZOS)
    except Exception as exc:
        print(
            f"Warning: Resize failed ({exc}).  Returning original image.",
            file=sys.stderr,
        )
        return img


def add_padding(img: Image.Image, padding: int) -> Image.Image:
    """Add transparent padding around an image.

    Useful for giving the embedded graphic breathing room on a slide
    without relying on CSS margins (which can behave inconsistently
    across slide layouts).

    Args:
        img: Source PIL Image (should be RGBA for transparency).
        padding: Number of transparent pixels to add on each side.

    Returns:
        A new image with the padding applied, or the original if
        ``padding`` is zero or negative.
    """
    if padding <= 0:
        return img

    new_w = img.size[0] + padding * 2
    new_h = img.size[1] + padding * 2

    try:
        # Create a fully transparent canvas and paste the image centered.
        padded = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
        padded.paste(img, (padding, padding))
        return padded
    except Exception as exc:
        print(
            f"Warning: Padding failed ({exc}).  Returning original image.",
            file=sys.stderr,
        )
        return img


def to_base64(img: Image.Image) -> str:
    """Encode a PIL Image as a PNG base64 data URI.

    Always outputs PNG regardless of the source format to preserve
    transparency and avoid JPEG compression artifacts on screenshots.

    Args:
        img: Source PIL Image.

    Returns:
        A complete ``data:image/png;base64,...`` URI string.

    Raises:
        SystemExit: If encoding fails (e.g. out of memory on very large images).
    """
    try:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except (OSError, MemoryError) as exc:
        print(f"Error: Base64 encoding failed: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Parse CLI arguments and run the crop → resize → encode pipeline."""
    parser = argparse.ArgumentParser(
        description="Crop, resize, and base64-encode a screenshot for slide embedding."
    )
    parser.add_argument("input", help="Path to the source image")
    parser.add_argument(
        "--max-size",
        type=int,
        default=800,
        help="Max pixels on longest side (default: 800)",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=0,
        help="Transparent padding in px to add around cropped image",
    )
    args = parser.parse_args()

    # Validate argument values.
    if args.max_size <= 0:
        print("Error: --max-size must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    if args.padding < 0:
        print("Error: --padding must be zero or a positive integer.", file=sys.stderr)
        sys.exit(1)

    p = Path(args.input)
    validate_input(p)

    img = safe_open_image(p)
    original_size = img.size

    # Step 1: Strip uniform-color borders (common on screenshots).
    img = auto_crop(img)
    cropped_size = img.size

    # Step 2: Scale down if the cropped result is still too large.
    img = resize(img, args.max_size)

    # Step 3: Optionally add transparent breathing room.
    if args.padding > 0:
        img = add_padding(img, args.padding)

    # Step 4: Encode to base64 and print the data URI.
    uri = to_base64(img)

    # Print size diagnostics to stderr so they don't pollute the URI output.
    print(f"# Original: {original_size[0]}x{original_size[1]}", file=sys.stderr)
    print(f"# Cropped:  {cropped_size[0]}x{cropped_size[1]}", file=sys.stderr)
    print(f"# Final:    {img.size[0]}x{img.size[1]}", file=sys.stderr)
    print(uri)


if __name__ == "__main__":
    main()
