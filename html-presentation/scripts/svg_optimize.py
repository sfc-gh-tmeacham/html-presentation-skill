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

import re
import sys
from pathlib import Path

# Maximum SVG file size we'll attempt to process (10 MB).  Larger files
# are likely not icons/logos and could cause excessive memory use during
# regex processing.
MAX_SVG_SIZE_BYTES: int = 10 * 1024 * 1024

# Regex patterns for entire elements that should be removed.  Each pattern
# uses DOTALL so `.*?` can span newlines inside the element.
STRIP_ELEMENTS: list[str] = [
    r"<metadata[\s>].*?</metadata>",           # Dublin Core / RDF metadata blocks
    r"<sodipodi:namedview[\s>].*?</sodipodi:namedview>",  # Inkscape canvas settings
    r"<namedview[\s>].*?</namedview>",          # Generic named-view variant
    r"<defs>\s*</defs>",                        # Empty <defs> wrappers (no actual defs)
    r"<defs/>",                                 # Self-closing empty <defs>
    r"<!--.*?-->",                              # All XML/HTML comments
]

# Regex patterns for individual attributes that should be stripped from tags.
# Each pattern starts with \s+ to also consume the leading whitespace.
STRIP_ATTRS: list[str] = [
    # Editor namespace declarations
    r'\s+xmlns:inkscape="[^"]*"',
    r'\s+xmlns:sodipodi="[^"]*"',
    r'\s+xmlns:sketch="[^"]*"',
    r'\s+xmlns:dc="[^"]*"',
    r'\s+xmlns:cc="[^"]*"',
    r'\s+xmlns:rdf="[^"]*"',
    # Editor-specific per-element attributes
    r'\s+inkscape:[a-z\-]+="[^"]*"',
    r'\s+sodipodi:[a-z\-]+="[^"]*"',
    r'\s+sketch:[a-z\-]+="[^"]*"',
    # Miscellaneous noise
    r'\s+xml:space="[^"]*"',                    # Redundant whitespace-handling hint
    r'\s+data-name="[^"]*"',                    # Design-tool layer names
]


def validate_input(input_path: Path) -> None:
    """Validate that the input is an existing SVG file within size limits.

    Args:
        input_path: Path to the source SVG.

    Raises:
        SystemExit: If the file is missing, not a file, not an SVG, empty,
            or exceeds the size limit.
    """
    if not input_path.exists():
        print(f"Error: '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"Error: '{input_path}' is not a regular file.", file=sys.stderr)
        sys.exit(1)

    if input_path.suffix.lower() != ".svg":
        print(
            f"Error: Expected an .svg file, got '{input_path.suffix}'.  "
            f"This tool only processes SVG files.",
            file=sys.stderr,
        )
        sys.exit(1)

    size = input_path.stat().st_size
    if size == 0:
        print(f"Error: '{input_path}' is empty (0 bytes).", file=sys.stderr)
        sys.exit(1)

    if size > MAX_SVG_SIZE_BYTES:
        mb = size / (1024 * 1024)
        print(
            f"Error: '{input_path}' is {mb:.1f} MB — exceeds the "
            f"{MAX_SVG_SIZE_BYTES // (1024 * 1024)} MB limit.",
            file=sys.stderr,
        )
        sys.exit(1)


def validate_svg_content(content: str, input_path: Path) -> None:
    """Basic sanity check that the file content looks like SVG.

    Args:
        content: The raw file text.
        input_path: Path to the file (for error messages).

    Raises:
        SystemExit: If the content does not contain an ``<svg`` tag.
    """
    if "<svg" not in content.lower():
        print(
            f"Error: '{input_path}' does not appear to contain SVG content "
            f"(no <svg> tag found).",
            file=sys.stderr,
        )
        sys.exit(1)


def optimize_svg(content: str) -> str:
    """Strip unnecessary metadata, comments, and attributes from SVG content.

    Applies two passes:
        1. Remove entire elements matching ``STRIP_ELEMENTS``.
        2. Remove individual attributes matching ``STRIP_ATTRS``.

    Finally collapses excessive blank lines and trailing whitespace.

    If a regex pattern fails (e.g. due to unusual encoding), that pattern
    is skipped with a warning rather than aborting the whole optimization.

    Args:
        content: Raw SVG source text.

    Returns:
        The optimized SVG source text.
    """
    # Pass 1: Remove whole elements (metadata blocks, comments, empty defs).
    for pattern in STRIP_ELEMENTS:
        try:
            content = re.sub(pattern, "", content, flags=re.DOTALL | re.IGNORECASE)
        except re.error as exc:
            # Log and skip — partial optimization is better than none.
            print(
                f"Warning: Regex failed for element pattern '{pattern[:40]}...': {exc}",
                file=sys.stderr,
            )

    # Pass 2: Remove individual editor-specific attributes from remaining tags.
    for pattern in STRIP_ATTRS:
        try:
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)
        except re.error as exc:
            print(
                f"Warning: Regex failed for attribute pattern '{pattern[:40]}...': {exc}",
                file=sys.stderr,
            )

    # Collapse runs of 3+ blank lines down to a single blank line.
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Strip trailing spaces/tabs on each line.
    content = re.sub(r"[ \t]+\n", "\n", content)

    # Ensure the file ends with exactly one newline.
    content = content.strip() + "\n"

    return content


def main() -> None:
    """Parse CLI arguments, optimize the SVG, and write or print the result."""
    if len(sys.argv) < 2:
        print("Usage: svg_optimize.py <input.svg> [output.svg]", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    validate_input(input_path)

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

    validate_svg_content(original, input_path)
    optimized = optimize_svg(original)

    # Verify the optimized output still contains the <svg> tag — if our
    # regex accidentally nuked it, fall back to the original content.
    if "<svg" not in optimized.lower():
        print(
            "Warning: Optimization removed the <svg> tag — this is a bug.  "
            "Falling back to the original unmodified SVG.",
            file=sys.stderr,
        )
        optimized = original

    # Calculate size savings for the diagnostics line.
    orig_size = len(original.encode("utf-8"))
    opt_size = len(optimized.encode("utf-8"))
    pct = ((orig_size - opt_size) / orig_size * 100) if orig_size > 0 else 0

    if len(sys.argv) >= 3:
        # Write to the specified output file.
        output_path = Path(sys.argv[2])

        # Ensure the output directory exists.
        if not output_path.parent.exists():
            print(
                f"Error: Output directory '{output_path.parent}' does not exist.",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            output_path.write_text(optimized, encoding="utf-8")
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
        print(optimized)


if __name__ == "__main__":
    main()
