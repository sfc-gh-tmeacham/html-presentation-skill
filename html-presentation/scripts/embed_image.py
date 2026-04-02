#!/usr/bin/env python3
"""Replace ``{{IMG:...}}`` placeholder tokens in an HTML file with base64 data URIs.

This script enables a two-phase build workflow for slide decks:

  1. **Author phase** — the LLM writes HTML with short placeholder tokens where
     images should appear.  No base64 ever enters the conversation context.
  2. **Embed phase** — this script scans the HTML, resolves each placeholder to
     a local file, resizes raster images, base64-encodes them, and writes the
     result back to the HTML file.  All heavy binary data stays in Python.

Placeholder syntax::

    {{IMG:path/to/image.png}}          — uses the default max-size (800 px)
    {{IMG:path/to/image.png|300}}      — caps the longest side at 300 px
    {{IMG:~/Downloads/logo.svg}}       — tilde expansion is supported
    {{IMG:./assets/hero.jpg|1200}}     — relative paths resolved from HTML dir

Placeholders are designed to appear inside ``src="..."`` attributes::

    <img src="{{IMG:photo.png}}" alt="Team photo">
    <img src="{{IMG:logo.svg|200}}" alt="Logo">

After running this script, the placeholder is replaced in-place with the full
``data:<mime>;base64,...`` URI.  The HTML file is overwritten.

Requires Pillow (installed automatically when invoked via run_script.py).

Usage::

    python run_script.py embed_image.py <deck.html> [--max-size 800] [--base-dir DIR]

Options::

    --max-size    Default max dimension for raster images (default: 800).
                  Per-token overrides (``{{IMG:file|N}}``) take precedence.
    --base-dir    Directory for resolving relative paths.  Defaults to the
                  directory containing the HTML file.
    --dry-run     Show what would be replaced without modifying the file.
"""

import argparse
import base64
import mimetypes
import os
import re
import sys
import tempfile
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

MIME_OVERRIDES: dict[str, str] = {
    ".svg": "image/svg+xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
}

RASTER_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

PLACEHOLDER_RE = re.compile(r"\{\{IMG:(.+?)\}\}")

MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024


def resolve_path(token_path: str, base_dir: Path) -> Path:
    """Resolve a placeholder path to an absolute filesystem path.

    Supports tilde expansion and relative paths resolved from *base_dir*.
    """
    expanded = os.path.expanduser(token_path)
    p = Path(expanded)
    if not p.is_absolute():
        p = base_dir / p
    return p.resolve()


def resize_and_encode(file_path: Path, max_size: int) -> tuple[str, int]:
    """Resize a raster image (if needed) and return a base64 data URI.

    Returns:
        A tuple of (data_uri, raw_byte_count).
    """
    if Image is None:
        print("Error: Pillow is required for raster image processing.", file=sys.stderr)
        sys.exit(1)

    img = Image.open(file_path)
    img.load()

    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    fmt = img.format or "PNG"
    if fmt.upper() == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buf = BytesIO()
    img.save(buf, format=fmt)
    raw = buf.getvalue()

    ext = file_path.suffix.lower()
    mime = MIME_OVERRIDES.get(ext) or mimetypes.guess_type(str(file_path))[0] or "image/png"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}", len(raw)


def encode_svg(file_path: Path) -> tuple[str, int]:
    """Read and base64-encode an SVG file.

    Returns:
        A tuple of (data_uri, raw_byte_count).
    """
    raw = file_path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}", len(raw)


def encode_file(file_path: Path, max_size: int) -> tuple[str, int]:
    """Encode any supported image file to a base64 data URI.

    Dispatches to SVG or raster handler based on extension.

    Returns:
        A tuple of (data_uri, raw_byte_count).
    """
    ext = file_path.suffix.lower()
    if ext == ".svg":
        return encode_svg(file_path)
    if ext in RASTER_EXTENSIONS:
        return resize_and_encode(file_path, max_size)
    raw = file_path.read_bytes()
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}", len(raw)


def parse_token(token_body: str) -> tuple[str, int | None]:
    """Parse the body of an ``{{IMG:...}}`` token.

    Args:
        token_body: The content between ``{{IMG:`` and ``}}``.

    Returns:
        A tuple of (file_path_str, per_token_max_size_or_None).
    """
    if "|" in token_body:
        parts = token_body.rsplit("|", 1)
        path_str = parts[0].strip()
        try:
            size = int(parts[1].strip())
        except ValueError:
            path_str = token_body.strip()
            size = None
        return path_str, size
    return token_body.strip(), None


def process_html(html: str, default_max_size: int, base_dir: Path, dry_run: bool = False) -> tuple[str, int, int, list[str]]:
    """Find and replace all ``{{IMG:...}}`` placeholders in the HTML.

    Uses a single ``re.sub`` pass with a replacement callback so the HTML
    string is only traversed once regardless of how many placeholders exist.

    Args:
        html: The full HTML string.
        default_max_size: Default max dimension for raster images.
        base_dir: Directory for resolving relative paths.
        dry_run: If True, don't replace — just report.

    Returns:
        A tuple of (modified_html, count_replaced, total_bytes_added, errors).
    """
    if not PLACEHOLDER_RE.search(html):
        return html, 0, 0, []

    count = 0
    total_bytes = 0
    errors: list[str] = []

    if dry_run:
        for match in PLACEHOLDER_RE.finditer(html):
            path_str, per_token_size = parse_token(match.group(1))
            max_size = per_token_size or default_max_size
            file_path = resolve_path(path_str, base_dir)
            if not file_path.exists():
                errors.append(f"  NOT FOUND: {path_str} (resolved: {file_path})")
            elif not file_path.is_file():
                errors.append(f"  NOT A FILE: {path_str} (resolved: {file_path})")
            elif file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                mb = file_path.stat().st_size / (1024 * 1024)
                errors.append(f"  TOO LARGE: {path_str} ({mb:.1f} MB)")
            else:
                print(f"  WOULD EMBED: {path_str} (max {max_size}px)")
                count += 1
        return html, count, 0, errors

    def _replace(match: re.Match) -> str:
        nonlocal count, total_bytes
        token_body = match.group(1)
        path_str, per_token_size = parse_token(token_body)
        max_size = per_token_size or default_max_size
        file_path = resolve_path(path_str, base_dir)

        if not file_path.exists():
            errors.append(f"  NOT FOUND: {path_str} (resolved: {file_path})")
            return match.group(0)
        if not file_path.is_file():
            errors.append(f"  NOT A FILE: {path_str} (resolved: {file_path})")
            return match.group(0)
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            mb = file_path.stat().st_size / (1024 * 1024)
            errors.append(f"  TOO LARGE: {path_str} ({mb:.1f} MB)")
            return match.group(0)

        try:
            data_uri, raw_bytes = encode_file(file_path, max_size)
        except Exception as exc:
            errors.append(f"  ENCODE ERROR: {path_str} — {exc}")
            return match.group(0)

        count += 1
        total_bytes += len(data_uri)
        return data_uri

    result = PLACEHOLDER_RE.sub(_replace, html)
    return result, count, total_bytes, errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace {{IMG:...}} placeholders with base64 data URIs."
    )
    parser.add_argument("html_file", help="Path to the HTML deck file")
    parser.add_argument(
        "--max-size", type=int, default=800,
        help="Default max dimension for raster images (default: 800)"
    )
    parser.add_argument(
        "--base-dir", type=str, default=None,
        help="Directory for resolving relative paths (default: HTML file's directory)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be replaced without modifying the file"
    )
    args = parser.parse_args()

    html_path = Path(args.html_file)
    if not html_path.is_file():
        print(f"Error: '{html_path}' not found or not a file.", file=sys.stderr)
        sys.exit(1)

    base_dir = Path(args.base_dir) if args.base_dir else html_path.parent
    base_dir = base_dir.resolve()

    html = html_path.read_text(encoding="utf-8")

    html, count, total_bytes, errors = process_html(
        html, args.max_size, base_dir, dry_run=args.dry_run
    )

    if errors:
        print("Errors:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)

    if args.dry_run:
        print(f"Dry run: {count} placeholder(s) would be replaced.")
        if errors:
            print(f"  {len(errors)} error(s) — see above.")
        return

    if count > 0:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=html_path.parent, prefix=".embed_tmp_", suffix=".html"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(html)
            os.replace(tmp_path, html_path)
        except Exception as exc:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            print(f"Error: Could not write '{html_path}': {exc}", file=sys.stderr)
            sys.exit(1)

    kb = total_bytes / 1024
    print(f"Embedded {count} image(s) ({kb:.1f} KB added to HTML).")
    if errors:
        print(f"  {len(errors)} placeholder(s) had errors — left unchanged.")


if __name__ == "__main__":
    main()
