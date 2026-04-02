#!/usr/bin/env python3
"""Optimize an SVG file by stripping unnecessary metadata, comments, and editor artifacts.

Targets bloat commonly left behind by Inkscape, Adobe Illustrator, Sketch,
and other vector editors.  The output is a cleaner, smaller SVG that
base64-encodes more compactly for slide-deck embedding.

Removes:
    - XML comments (``<!-- ... -->``)
    - ``<metadata>``, ``<sodipodi:namedview>``, and empty ``<defs>`` elements
    - Editor-specific namespace declarations (Inkscape, Sodipodi, Sketch, etc.)
    - ``xml:space`` and ``data-name`` attributes
    - Redundant blank lines and trailing whitespace

Usage::

    python svg_optimize.py <input> [<output>]

If ``<output>`` is omitted the optimized SVG is printed to stdout.

Examples::

    python svg_optimize.py logo_raw.svg logo_clean.svg
    python svg_optimize.py icon.svg | scripts/img_to_base64.py /dev/stdin
"""

import argparse
import contextlib
import os
import re
import sys
import tempfile
from pathlib import Path

# Maximum SVG file size we'll attempt to process (10 MB).  Larger files
# are likely not icons/logos and could cause excessive memory use during
# regex processing.
MAX_SVG_SIZE_BYTES: int = 10 * 1024 * 1024

# Number of bytes to scan when checking for the <svg> tag.
_SVG_TAG_SCAN_BYTES = 8192

# Regex patterns for entire elements that should be removed.  Each pattern
# uses DOTALL so `.*?` can span newlines inside the element.
STRIP_ELEMENTS: list[str] = [
    r"<metadata[\s>].*?</metadata>",           # Dublin Core / RDF metadata blocks
    r"<metadata\s*/>",                          # Self-closing variant
    r"<sodipodi:namedview[\s>].*?</sodipodi:namedview>",  # Inkscape canvas settings
    r"<sodipodi:namedview\s*/>",                # Self-closing variant
    r"<namedview[\s>].*?</namedview>",          # Generic named-view variant
    r"<namedview\s*/>",                         # Self-closing variant
    r"<defs[^>]*>\s*</defs>",                   # Empty <defs> wrappers (no actual defs)
    r"<defs\s*/>",                              # Self-closing: <defs/> and <defs />
    r"<!--.*?-->",                              # All XML/HTML comments
]

# Regex patterns for individual attributes that should be stripped from tags.
# Each pattern starts with \s+ to also consume the leading whitespace.
STRIP_ATTRS: list[str] = [
    # Editor namespace declarations (double or single quoted)
    r"\s+xmlns:inkscape=(?:\"[^\"]*\"|'[^']*')",
    r"\s+xmlns:sodipodi=(?:\"[^\"]*\"|'[^']*')",
    r"\s+xmlns:sketch=(?:\"[^\"]*\"|'[^']*')",
    r"\s+xmlns:dc=(?:\"[^\"]*\"|'[^']*')",
    r"\s+xmlns:cc=(?:\"[^\"]*\"|'[^']*')",
    r"\s+xmlns:rdf=(?:\"[^\"]*\"|'[^']*')",
    # Editor-specific per-element attributes
    r"\s+inkscape:[a-zA-Z0-9_\-]+=(?:\"[^\"]*\"|'[^']*')",
    r"\s+sodipodi:[a-zA-Z0-9_\-]+=(?:\"[^\"]*\"|'[^']*')",
    r"\s+sketch:[a-zA-Z0-9_\-]+=(?:\"[^\"]*\"|'[^']*')",
    # Miscellaneous noise
    r"\s+xml:space=(?:\"[^\"]*\"|'[^']*')",    # Redundant whitespace-handling hint
    r"\s+data-name=(?:\"[^\"]*\"|'[^']*')",    # Design-tool layer names
]

# Pre-compiled versions of the above patterns for efficient repeated use.
_STRIP_ELEMENTS_RE: list[re.Pattern[str]] = [
    re.compile(p, re.DOTALL | re.IGNORECASE) for p in STRIP_ELEMENTS
]
_STRIP_ATTRS_RE: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in STRIP_ATTRS
]

_BLANK_LINES_RE = re.compile(r"\n{3,}")
_TRAILING_WS_RE = re.compile(r"[ \t]+\n")


def validate_input(input_path: Path) -> None:
    """Validate that the input is an existing SVG file within size limits.

    Args:
        input_path: Path to the source SVG.

    Raises:
        ValueError: If the file is missing, not a file, not an SVG, empty,
            or exceeds the size limit.
    """
    if not input_path.exists():
        raise ValueError(f"Error: '{input_path}' not found.")

    if not input_path.is_file():
        raise ValueError(f"Error: '{input_path}' is not a regular file.")

    if input_path.suffix.lower() != ".svg":
        raise ValueError(
            f"Error: Expected an .svg file, got '{input_path.suffix}'.  "
            f"This tool only processes SVG files."
        )

    size = input_path.stat().st_size
    if size == 0:
        raise ValueError(f"Error: '{input_path}' is empty (0 bytes).")

    if size > MAX_SVG_SIZE_BYTES:
        mb = size / (1024 * 1024)
        raise ValueError(
            f"Error: '{input_path}' is {mb:.1f} MB — exceeds the "
            f"{MAX_SVG_SIZE_BYTES // (1024 * 1024)} MB limit."
        )


def validate_svg_content(content: str, input_path: Path) -> None:
    """Basic sanity check that the file content looks like SVG.

    Args:
        content: The raw file text.
        input_path: Path to the file (for error messages).

    Raises:
        ValueError: If the content does not contain an ``<svg`` tag.
    """
    if "<svg" not in content[:_SVG_TAG_SCAN_BYTES].lower():
        raise ValueError(
            f"Error: '{input_path}' does not appear to contain SVG content "
            f"(no <svg> tag found)."
        )


def optimize_svg(content: str) -> str:
    """Strip unnecessary metadata, comments, and attributes from SVG content.

    Applies two passes:
        1. Remove entire elements matching ``STRIP_ELEMENTS``.
        2. Remove individual attributes matching ``STRIP_ATTRS``.

    Finally collapses excessive blank lines and trailing whitespace.

    Patterns are pre-compiled at module load; no per-call error handling is needed.

    Args:
        content: Raw SVG source text.

    Returns:
        The optimized SVG source text.
    """
    # Pass 1: Remove whole elements (metadata blocks, comments, empty defs).
    for pattern in _STRIP_ELEMENTS_RE:
        # Pre-compiled pattern; re.error would only occur at compile time
        content = pattern.sub("", content)

    # Pass 2: Remove individual editor-specific attributes from remaining tags.
    for pattern in _STRIP_ATTRS_RE:
        # Pre-compiled pattern; re.error would only occur at compile time
        content = pattern.sub("", content)

    # Collapse runs of 3+ blank lines down to a single blank line.
    content = _BLANK_LINES_RE.sub("\n\n", content)

    # Strip trailing spaces/tabs on each line.
    content = _TRAILING_WS_RE.sub("\n", content)

    # Ensure the file ends with exactly one newline.
    content = content.strip() + "\n"

    return content


def _write_atomic(path: Path, content: str) -> None:
    """Write *content* to *path* atomically using a sibling temp file."""
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, prefix=".svgopt_tmp_", suffix=".svg"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except OSError:
        with contextlib.suppress(OSError):
            os.close(tmp_fd)
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


def main() -> None:
    """Parse CLI arguments, optimize the SVG, and write or print the result."""
    parser = argparse.ArgumentParser(
        description="Optimize an SVG by stripping editor metadata and attributes."
    )
    parser.add_argument("input", help="Path to the source SVG")
    parser.add_argument(
        "output", nargs="?", help="Output path (omit to print to stdout)"
    )
    parser.add_argument("--version", action="version", version="svg_optimize 1.0")
    args = parser.parse_args()

    input_path = Path(args.input)
    try:
        validate_input(input_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if args.output and Path(args.output).resolve() == input_path.resolve():
        print("Error: input and output paths resolve to the same file.", file=sys.stderr)
        sys.exit(1)

    # Read the source SVG with explicit UTF-8 encoding.
    try:
        original = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(
            f"Error: '{input_path}' contains invalid UTF-8: {exc}.  "
            f"SVG files must be valid UTF-8 or ASCII.",
            file=sys.stderr,
        )
        sys.exit(1)
    except OSError as exc:
        print(f"Error: Could not read '{input_path}': {exc}", file=sys.stderr)
        sys.exit(1)

    orig_size = len(original.encode("utf-8"))

    try:
        validate_svg_content(original, input_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    optimized = optimize_svg(original)

    # Verify the optimized output still contains the <svg> tag — if our
    # regex accidentally nuked it, fall back to the original content.
    if "<svg" not in optimized[:_SVG_TAG_SCAN_BYTES].lower():
        print(
            "Warning: Optimization removed the <svg> tag — this is a bug.  "
            "Falling back to the original unmodified SVG.",
            file=sys.stderr,
        )
        optimized = original

    # Calculate size savings for the diagnostics line.
    opt_size = len(optimized.encode("utf-8"))
    pct = ((orig_size - opt_size) / orig_size * 100) if orig_size > 0 else 0

    if args.output:
        output_path = Path(args.output)

        # Ensure the output directory exists.
        if not output_path.parent.exists():
            print(
                f"Error: Output directory '{output_path.parent}' does not exist.",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            _write_atomic(output_path, optimized)
        except OSError as exc:
            print(f"Error: Could not write to '{output_path}': {exc}", file=sys.stderr)
            sys.exit(1)

        print(
            f"Optimized: {orig_size:,} → {opt_size:,} bytes "
            f"({pct:.1f}% smaller) → {output_path}",
            file=sys.stderr,
        )
    else:
        # No output file — print diagnostics to stderr, SVG to stdout.
        print(
            f"# Optimized: {orig_size:,} → {opt_size:,} bytes ({pct:.1f}% smaller)",
            file=sys.stderr,
        )
        sys.stdout.write(optimized)


if __name__ == "__main__":
    main()
