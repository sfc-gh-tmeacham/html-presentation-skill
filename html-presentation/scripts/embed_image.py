#!/usr/bin/env python3
"""Replace placeholder tokens in an HTML slide deck with embedded assets.

This script enables a two-phase build workflow:

  1. **Author phase** — the LLM writes HTML with short placeholder tokens.
     No base64 or SVG markup ever enters the conversation context.
  2. **Embed phase** — this script resolves each token, embeds the asset,
     and writes the result back.  All heavy data stays in Python.

Supported tokens
----------------

``{{IMG:path}}`` / ``{{IMG:path|max-px}}``
    Resize (if needed) and base64-encode a raster image or SVG.  Replaces
    only the ``src`` attribute value — keep it inside ``<img src="...">``::

        <img src="{{IMG:photo.png}}" alt="Team photo">
        <img src="{{IMG:logo.svg|200}}" alt="Logo">

``{{SNOWFLAKE_LOGO}}``
    Inject the Snowflake mark + wordmark as a pre-validated inline SVG block.
    Place as a bare standalone token (not inside an ``<img>``).

``{{SVG_INLINE:path}}`` / ``{{SVG_INLINE:path|css-style}}``
    Inline a user-provided SVG diagram directly as an ``<svg>`` element.
    Safer and more flexible than ``{{IMG:...}}`` for SVGs because:
    - No base64 overhead (SVGs are text)
    - Can inherit CSS custom properties such as ``var(--accent)``
    - Directly styleable with CSS
    The optional second argument is a CSS style string injected onto the
    root ``<svg>`` element::

        {{SVG_INLINE:architecture-diagram.svg}}
        {{SVG_INLINE:chart.svg|max-height:60vh;width:100%}}

    User-provided SVGs are sanitized: ``<script>`` elements, ``on*`` event
    handlers, ``javascript:`` URIs, and XML declarations are stripped.
    Use ``{{IMG:path.svg}}`` instead when you need the SVG inside an
    ``<img>`` tag or when the SVG should not be part of the DOM.

``{{LOGO_INLINE:path}}`` / ``{{LOGO_INLINE:path|css-style}}``
    Inline a user-provided SVG **logo or decorative image** as an ``<svg>``
    element.  Identical to ``{{SVG_INLINE:...}}`` except that ``role="img"``
    is automatically stamped onto the root ``<svg>`` tag.  This signals to
    ``validate_deck.py`` that the SVG is a logo and should be skipped by
    geometry checks (aspect-ratio, viewBox gaps, text overflow, etc.)::

        {{LOGO_INLINE:customer-logo.svg}}
        {{LOGO_INLINE:partner-logo.svg|height:60px;display:block;margin:0 auto}}

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

_FMT_MIME: dict[str, str] = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "GIF": "image/gif",
    "WEBP": "image/webp",
    "BMP": "image/bmp",
    "TIFF": "image/tiff",
}

RASTER_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

PLACEHOLDER_RE = re.compile(r"\{\{IMG:(.+?)\}\}")
LOGO_PLACEHOLDER_RE = re.compile(r"\{\{SNOWFLAKE_LOGO\}\}")
SVG_INLINE_RE = re.compile(r"\{\{SVG_INLINE:(.+?)\}\}")
LOGO_INLINE_RE = re.compile(r"\{\{LOGO_INLINE:(.+?)\}\}")

_SVG_SCRIPT_RE = re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE)
_SVG_EVENT_RE = re.compile(r"\s+on\w+\s*=\s*(?:(?P<q>['\"]).*?(?P=q)|\S+)", re.IGNORECASE)
_SVG_JS_URI_RE = re.compile(r"javascript\s*:[^\"'\s>]*", re.IGNORECASE)
_SVG_XML_DECL_RE = re.compile(r"<\?xml[^?]*\?>", re.IGNORECASE)
_SVG_DOCTYPE_RE = re.compile(r"<!DOCTYPE[^>]*>", re.IGNORECASE)
_SVG_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_SVG_STYLE_ATTR_RE = re.compile(r"(<svg\b[^>]*?)\sstyle=(?P<q>['\"]).*?(?P=q)", re.IGNORECASE)
_SVG_ROLE_ATTR_RE = re.compile(r"(<svg\b[^>]*?)\srole=(?P<q>['\"]).*?(?P=q)", re.IGNORECASE)
_SVG_TAG_RE = re.compile(r"(<svg\b)", re.IGNORECASE)

LOGO_SVG_STYLE = (
    'style="display:block;margin:0 auto clamp(10px,2vh,18px);'
    'height:clamp(44px,7vh,80px);width:auto;"'
)
LOGO_SVG_HEADER = (
    '<svg viewBox="0 0 184 44" xmlns="http://www.w3.org/2000/svg" '
    'aria-label="Snowflake" role="img" ' + LOGO_SVG_STYLE + ">\n"
    '  <g fill="#29B5E8" fill-rule="nonzero" transform="translate(-0.002027,0.531250)">\n'
)
LOGO_SVG_FOOTER = "  </g>\n</svg>"

_LOGO_INLINE: str | None = None


def _get_logo_inline() -> str:
    """Read assets/snowflake-logo.svg and return a ready-to-inline SVG block.

    The SVG file is located at ``../assets/snowflake-logo.svg`` relative to
    this script.  The XML declaration, Sketch metadata, and ``id`` attributes
    are stripped; the prescribed CSS sizing and accessibility attributes are
    applied.

    The result is cached in-process after the first read.
    """
    global _LOGO_INLINE
    if _LOGO_INLINE is not None:
        return _LOGO_INLINE

    script_dir = Path(__file__).resolve().parent
    logo_path = script_dir.parent / "assets" / "snowflake-logo.svg"
    if not logo_path.is_file():
        raise FileNotFoundError(f"Snowflake logo not found at expected path: {logo_path}")

    raw = logo_path.read_text(encoding="utf-8")
    paths = re.findall(r'<path d="([^"]+)"', raw)
    if len(paths) != 16:
        raise ValueError(
            f"Expected 16 <path> elements in snowflake-logo.svg, found {len(paths)}. "
            "The logo file may be corrupt or have been modified."
        )

    path_lines = "\n".join(f'    <path d="{d}"/>' for d in paths)
    _LOGO_INLINE = LOGO_SVG_HEADER + path_lines + "\n" + LOGO_SVG_FOOTER
    return _LOGO_INLINE

def _sanitize_svg(text: str) -> str:
    """Strip dangerous constructs from a user-provided SVG string.

    Removes: XML/DOCTYPE declarations, HTML comments, ``<script>`` elements,
    ``on*`` event-handler attributes, and ``javascript:`` URI values.
    The resulting string is safe to inject directly into HTML.
    """
    text = _SVG_XML_DECL_RE.sub("", text)
    text = _SVG_DOCTYPE_RE.sub("", text)
    text = _SVG_COMMENT_RE.sub("", text)
    text = _SVG_SCRIPT_RE.sub("", text)
    text = _SVG_EVENT_RE.sub("", text)
    text = _SVG_JS_URI_RE.sub("", text)
    return text.strip()


def _inject_svg_style(svg_text: str, style: str) -> str:
    """Merge *style* into the root ``<svg>`` element's style attribute.

    If a ``style`` attribute already exists on the root ``<svg>`` tag it is
    replaced; otherwise a new one is added.  Only the first ``<svg>`` tag is
    touched.
    """
    replacement = rf'\1 style="{style}"'
    result, n = _SVG_STYLE_ATTR_RE.subn(replacement, svg_text, count=1)
    if n == 0:
        result = _SVG_TAG_RE.sub(rf'\1 style="{style}"', svg_text, count=1)
    return result


def _inject_svg_role_img(svg_text: str) -> str:
    """Stamp role="img" onto the root ``<svg>`` element.

    If a role attribute already exists it is replaced; otherwise a new one
    is added.  Only the first ``<svg>`` tag is touched.
    """
    result, n = _SVG_ROLE_ATTR_RE.subn(r'\1 role="img"', svg_text, count=1)
    if n == 0:
        result = _SVG_TAG_RE.sub(r'\1 role="img"', svg_text, count=1)
    return result


def _inline_user_svg(file_path: Path, style: str | None) -> str:
    """Read, sanitize, and optionally restyle a user-provided SVG file.

    Returns the SVG markup ready for direct inline embedding in HTML.
    """
    raw = file_path.read_text(encoding="utf-8")
    sanitized = _sanitize_svg(raw)
    if style:
        sanitized = _inject_svg_style(sanitized, style)
    return sanitized


def _parse_svg_token(token_body: str) -> tuple[str, str | None]:
    """Parse ``{{SVG_INLINE:path}}`` / ``{{LOGO_INLINE:path}}`` token bodies.

    Returns:
        A tuple of (file_path_str, css_style_or_None).
    """
    if "|" in token_body:
        path_str, _, style_str = token_body.partition("|")
        return path_str.strip(), style_str.strip() or None
    return token_body.strip(), None


_parse_svg_inline_token = _parse_svg_token


def process_svg_inline(
    html: str, base_dir: Path, dry_run: bool = False
) -> tuple[str, int, list[str]]:
    """Replace all ``{{SVG_INLINE:...}}`` tokens with sanitized inline SVG.

    Returns:
        A tuple of (modified_html, count_replaced, errors).
    """
    errors: list[str] = []
    count = 0

    if dry_run:
        for match in SVG_INLINE_RE.finditer(html):
            path_str, style = _parse_svg_token(match.group(1))
            file_path, resolve_err = resolve_path(path_str, base_dir)
            if resolve_err:
                errors.append(resolve_err)
            elif not file_path.exists():
                errors.append(f"NOT FOUND: {path_str} (resolved: {file_path})")
            elif file_path.suffix.lower() != ".svg":
                errors.append(f"NOT SVG: {path_str} — {{{{SVG_INLINE}}}} only supports .svg files")
            else:
                print(f"  WOULD INLINE SVG: {path_str}" + (f" (style: {style})" if style else ""))
                count += 1
        return html, count, errors

    def _replace(match: re.Match) -> str:
        nonlocal count
        path_str, style = _parse_svg_token(match.group(1))
        file_path, resolve_err = resolve_path(path_str, base_dir)

        if resolve_err:
            errors.append(resolve_err)
            return match.group(0)
        if not file_path.exists():
            errors.append(f"NOT FOUND: {path_str} (resolved: {file_path})")
            return match.group(0)
        if file_path.suffix.lower() != ".svg":
            errors.append(f"NOT SVG: {path_str} — {{{{SVG_INLINE}}}} only supports .svg files")
            return match.group(0)
        st = file_path.stat()
        if st.st_size > MAX_FILE_SIZE_BYTES:
            mb = st.st_size / (1024 * 1024)
            errors.append(f"TOO LARGE: {path_str} ({mb:.1f} MB)")
            return match.group(0)

        try:
            inline = _inline_user_svg(file_path, style)
        except Exception as exc:
            errors.append(f"SVG_INLINE ERROR: {path_str} — {exc}")
            return match.group(0)

        count += 1
        return inline

    result = SVG_INLINE_RE.sub(_replace, html)
    return result, count, errors


def process_logo_inline(
    html: str, base_dir: Path, dry_run: bool = False
) -> tuple[str, int, list[str]]:
    """Replace all ``{{LOGO_INLINE:...}}`` tokens with sanitized inline SVG.

    Identical to :func:`process_svg_inline` except ``role="img"`` is stamped
    onto the root ``<svg>`` tag so that ``validate_deck.py`` skips geometry
    checks (aspect-ratio, viewBox gaps, text overflow, etc.) for logo SVGs.

    Returns:
        A tuple of (modified_html, count_replaced, errors).
    """
    errors: list[str] = []
    count = 0

    if dry_run:
        for match in LOGO_INLINE_RE.finditer(html):
            path_str, style = _parse_svg_token(match.group(1))
            file_path, resolve_err = resolve_path(path_str, base_dir)
            if resolve_err:
                errors.append(resolve_err)
            elif not file_path.exists():
                errors.append(f"NOT FOUND: {path_str} (resolved: {file_path})")
            elif file_path.suffix.lower() != ".svg":
                errors.append(f"NOT SVG: {path_str} — {{{{LOGO_INLINE}}}} only supports .svg files")
            else:
                print(f"  WOULD INLINE LOGO SVG: {path_str}" + (f" (style: {style})" if style else ""))
                count += 1
        return html, count, errors

    def _replace(match: re.Match) -> str:
        nonlocal count
        path_str, style = _parse_svg_token(match.group(1))
        file_path, resolve_err = resolve_path(path_str, base_dir)

        if resolve_err:
            errors.append(resolve_err)
            return match.group(0)
        if not file_path.exists():
            errors.append(f"NOT FOUND: {path_str} (resolved: {file_path})")
            return match.group(0)
        if file_path.suffix.lower() != ".svg":
            errors.append(f"NOT SVG: {path_str} — {{{{LOGO_INLINE}}}} only supports .svg files")
            return match.group(0)
        st = file_path.stat()
        if st.st_size > MAX_FILE_SIZE_BYTES:
            mb = st.st_size / (1024 * 1024)
            errors.append(f"TOO LARGE: {path_str} ({mb:.1f} MB)")
            return match.group(0)

        try:
            inline = _inline_user_svg(file_path, style)
            inline = _inject_svg_role_img(inline)
        except Exception as exc:
            errors.append(f"LOGO_INLINE ERROR: {path_str} — {exc}")
            return match.group(0)

        count += 1
        return inline

    result = LOGO_INLINE_RE.sub(_replace, html)
    return result, count, errors


_TMP_DIRS: frozenset[Path] = frozenset({
    Path("/tmp").resolve(),
    Path(tempfile.gettempdir()).resolve(),
})

MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024


def resolve_path(token_path: str, base_dir: Path) -> tuple[Path | None, str | None]:
    """Resolve a placeholder path to an absolute filesystem path.

    Supports tilde expansion, relative paths resolved from *base_dir*, and
    absolute paths inside the system temp directory (e.g. /tmp).
    Returns (path, None) on success or (None, error_message) on failure.
    """
    path_str = token_path.strip()
    if path_str.startswith("~"):
        expanded = Path(path_str).expanduser().resolve()
        home = Path.home().resolve()
        if not expanded.is_relative_to(home):
            return None, f"SECURITY: tilde path '{token_path}' escapes home directory"
        if not expanded.is_file():
            return None, f"NOT FOUND: {token_path!r}"
        return expanded, None

    p = Path(path_str).expanduser()
    if not p.is_absolute():
        p = base_dir / p
    resolved = p.resolve()
    if any(resolved.is_relative_to(tmp) for tmp in _TMP_DIRS):
        if not resolved.is_file():
            return None, f"NOT FOUND: {token_path!r}"
        return resolved, None

    try:
        resolved.relative_to(base_dir.resolve())
    except ValueError:
        return None, f"SECURITY: path '{token_path}' escapes base directory"
    return resolved, None


def resize_and_encode(file_path: Path, max_size: int) -> tuple[str, int]:
    """Resize a raster image (if needed) and return a base64 data URI.

    Returns:
        A tuple of (data_uri, raw_byte_count).
    """
    if Image is None:
        raise RuntimeError("Pillow is required for --max-size. Install with: pip install Pillow")

    img = Image.open(file_path)
    if img.width * img.height > Image.MAX_IMAGE_PIXELS:
        raise ValueError(f"Image '{file_path.name}' exceeds maximum pixel count")
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
    mime = _FMT_MIME.get(fmt.upper()) or MIME_OVERRIDES.get(ext) or "image/png"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}", len(raw)


def encode_svg(file_path: Path) -> tuple[str, int]:
    """Read and base64-encode an SVG file.

    Returns:
        A tuple of (data_uri, raw_byte_count).
    """
    raw = file_path.read_bytes()
    print(f"Warning: embedding SVG '{file_path.name}' without sanitization — ensure it is trusted", file=sys.stderr)
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}", len(raw)


def encode_file(file_path: Path, max_size: int) -> tuple[str, int]:
    """Encode any supported image file to a data URI.

    Dispatches to SVG or raster handler based on extension.

    Returns:
        A tuple of (data_uri, raw_byte_count).
    """
    ext = file_path.suffix.lower()
    if ext == ".svg":
        return encode_svg(file_path)
    if ext in RASTER_EXTENSIONS:
        return resize_and_encode(file_path, max_size)
    allowed = RASTER_EXTENSIONS | {".svg"}
    raise ValueError(f"Unsupported file type '{ext}'; allowed: {', '.join(sorted(allowed))}")


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
            if size <= 0:
                size = None
        except ValueError:
            path_str = token_body.strip()
            size = None
        return path_str, size
    return token_body.strip(), None


def process_logo(html: str, dry_run: bool = False) -> tuple[str, int, list[str]]:
    """Replace all ``{{SNOWFLAKE_LOGO}}`` tokens with an inline SVG block.

    Returns:
        A tuple of (modified_html, count_replaced, errors).
    """
    count = len(LOGO_PLACEHOLDER_RE.findall(html))
    if count == 0:
        return html, 0, []

    if dry_run:
        print(f"  WOULD EMBED: {{{{SNOWFLAKE_LOGO}}}} ({count} occurrence(s))")
        return html, count, []

    errors: list[str] = []
    try:
        inline_svg = _get_logo_inline()
    except (FileNotFoundError, ValueError) as exc:
        errors.append(f"SNOWFLAKE_LOGO ERROR: {exc}")
        return html, 0, errors

    result = LOGO_PLACEHOLDER_RE.sub(inline_svg, html)
    return result, count, errors


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
    html, logo_count, logo_errors = process_logo(html, dry_run=dry_run)
    html, svg_inline_count, svg_inline_errors = process_svg_inline(html, base_dir, dry_run=dry_run)
    html, logo_inline_count, logo_inline_errors = process_logo_inline(html, base_dir, dry_run=dry_run)

    count = 0
    total_bytes = 0
    errors: list[str] = list(logo_errors) + list(svg_inline_errors) + list(logo_inline_errors)

    if dry_run:
        for match in PLACEHOLDER_RE.finditer(html):
            path_str, per_token_size = parse_token(match.group(1))
            max_size = per_token_size if per_token_size is not None else default_max_size
            file_path, resolve_err = resolve_path(path_str, base_dir)
            if resolve_err:
                errors.append(resolve_err)
            elif not file_path.exists():
                errors.append(f"NOT FOUND: {path_str} (resolved: {file_path})")
            elif not file_path.is_file():
                errors.append(f"NOT A FILE: {path_str} (resolved: {file_path})")
            else:
                st = file_path.stat()
                if st.st_size > MAX_FILE_SIZE_BYTES:
                    mb = st.st_size / (1024 * 1024)
                    errors.append(f"TOO LARGE: {path_str} ({mb:.1f} MB)")
                else:
                    print(f"  WOULD EMBED: {path_str} (max {max_size}px)")
                    count += 1
        return html, count, 0, errors

    def _replace(match: re.Match) -> str:
        nonlocal count, total_bytes
        token_body = match.group(1)
        path_str, per_token_size = parse_token(token_body)
        max_size = per_token_size if per_token_size is not None else default_max_size
        file_path, resolve_err = resolve_path(path_str, base_dir)

        if resolve_err:
            errors.append(resolve_err)
            return match.group(0)
        if not file_path.exists():
            errors.append(f"NOT FOUND: {path_str} (resolved: {file_path})")
            return match.group(0)
        if not file_path.is_file():
            errors.append(f"NOT A FILE: {path_str} (resolved: {file_path})")
            return match.group(0)
        st = file_path.stat()
        if st.st_size > MAX_FILE_SIZE_BYTES:
            mb = st.st_size / (1024 * 1024)
            errors.append(f"TOO LARGE: {path_str} ({mb:.1f} MB)")
            return match.group(0)

        try:
            data_uri, byte_count = encode_file(file_path, max_size)
        except Exception as exc:
            errors.append(f"ENCODE ERROR: {path_str} — {exc}")
            return match.group(0)

        count += 1
        total_bytes += byte_count
        return data_uri

    result = PLACEHOLDER_RE.sub(_replace, html)
    return result, count + logo_count + svg_inline_count + logo_inline_count, total_bytes, errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace {{IMG:...}} and {{SNOWFLAKE_LOGO}} placeholders in an HTML deck."
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

    if args.max_size <= 0:
        parser.error("--max-size must be a positive integer")

    html_path = Path(args.html_file)
    if not html_path.is_file():
        print(f"Error: '{html_path}' not found or not a file.", file=sys.stderr)
        sys.exit(1)

    base_dir = Path(args.base_dir).expanduser().resolve() if args.base_dir else html_path.parent.resolve()

    if args.base_dir and not base_dir.is_dir():
        print(f"Error: --base-dir '{base_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    if args.max_size and Image is None:
        print("Error: --max-size requires Pillow. Install with: pip install Pillow", file=sys.stderr)
        sys.exit(1)

    try:
        html = html_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"Error: '{html_path}' is not valid UTF-8.", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error: Could not read '{html_path}': {exc}", file=sys.stderr)
        sys.exit(1)

    html, count, total_bytes, errors = process_html(
        html, args.max_size, base_dir, dry_run=args.dry_run
    )

    if errors:
        print("Errors:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)

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
    print(f"Embedded {count} asset(s) ({kb:.1f} KB added to HTML).")
    if errors:
        print(f"  {len(errors)} placeholder(s) had errors — left unchanged.")


if __name__ == "__main__":
    main()
