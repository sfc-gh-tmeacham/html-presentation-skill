#!/usr/bin/env python3
"""Convert any image file (raster or SVG) to a base64 data URI string.

Reads the file in binary mode, base64-encodes it, and prints a complete
``data:<mime>;base64,...`` URI to stdout — ready to paste directly into
an ``<img src="...">`` tag in the slide-deck HTML.

Usage::

    python img_to_base64.py <file>

Example::

    python img_to_base64.py company_logo.svg
    # → data:image/svg+xml;base64,PD94bWwg...
"""

import base64
import mimetypes
import sys
from pathlib import Path

# Explicit MIME overrides so we don't rely on the OS mime database, which
# can be incomplete or inconsistent across platforms.
MIME_OVERRIDES: dict[str, str] = {
    ".svg": "image/svg+xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
}

# Maximum file size we'll attempt to encode (20 MB).  Larger files almost
# certainly indicate the wrong input and would produce enormous data URIs.
MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024


def validate_input(file_path: Path) -> None:
    """Validate that the input file exists, is a regular file, and is within size limits.

    Args:
        file_path: Path to the image file.

    Raises:
        SystemExit: If the file is missing, not a regular file, empty,
            or exceeds the size limit.
    """
    if not file_path.exists():
        print(f"Error: '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    if not file_path.is_file():
        print(f"Error: '{file_path}' is not a regular file.", file=sys.stderr)
        sys.exit(1)

    size = file_path.stat().st_size
    if size == 0:
        print(f"Error: '{file_path}' is empty (0 bytes).", file=sys.stderr)
        sys.exit(1)

    if size > MAX_FILE_SIZE_BYTES:
        mb = size / (1024 * 1024)
        print(
            f"Error: '{file_path}' is {mb:.1f} MB — exceeds the "
            f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit.  "
            f"Resize the image first with resize_image.py.",
            file=sys.stderr,
        )
        sys.exit(1)


def img_to_base64(file_path: Path) -> str:
    """Convert an image file to a base64 data URI.

    Args:
        file_path: Filesystem path to the image (raster or SVG).

    Returns:
        A complete data URI string, e.g.
        ``data:image/png;base64,iVBORw0KGgo...``.

    Raises:
        SystemExit: If the file cannot be read or encoded.
    """
    # Determine the MIME type — prefer our explicit map, fall back to the
    # standard library's guess, and default to a generic binary type.
    ext = file_path.suffix.lower()
    mime = (
        MIME_OVERRIDES.get(ext)
        or mimetypes.guess_type(str(file_path))[0]
        or "application/octet-stream"
    )

    # Warn if the MIME type is generic — the file may not be a real image.
    if mime == "application/octet-stream":
        print(
            f"Warning: Unrecognized extension '{ext}'.  "
            f"The data URI will use 'application/octet-stream' as the MIME type.  "
            f"The browser may not render it as an image.",
            file=sys.stderr,
        )

    # Read raw bytes and encode to base64 ASCII.
    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        print(f"Error: Could not read '{file_path}': {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        encoded = base64.b64encode(raw).decode("ascii")
    except (MemoryError, Exception) as exc:
        print(f"Error: Base64 encoding failed: {exc}", file=sys.stderr)
        sys.exit(1)

    return f"data:{mime};base64,{encoded}"


def main() -> None:
    """Parse the single CLI argument and print the data URI to stdout."""
    if len(sys.argv) != 2:
        print("Usage: img_to_base64.py <image_file>", file=sys.stderr)
        sys.exit(1)

    p = Path(sys.argv[1])
    validate_input(p)

    uri = img_to_base64(p)

    # Sanity check: a valid data URI should start with "data:" and contain
    # base64 content after the comma.
    if not uri.startswith("data:") or "," not in uri:
        print("Error: Generated data URI appears malformed.", file=sys.stderr)
        sys.exit(1)

    print(uri)


if __name__ == "__main__":
    main()
