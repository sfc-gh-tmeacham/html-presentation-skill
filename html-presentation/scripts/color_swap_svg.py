#!/usr/bin/env python3
"""Replace fill, stroke, and stop-color values in an SVG file.

Designed to make logos and icons visible on the slide deck's dark
(``#0a0a0a``) background by swapping dark fills to light ones, or to
recolor assets to match the deck's accent color.

Handles multiple color representations:
    - Shorthand hex (``#000``)
    - Full hex (``#000000``)
    - Named colors (``black``, ``white``)
    - ``rgb()`` functional notation

Usage::

    python color_swap_svg.py <input.svg> [<output.svg>] \\
        [--from-color "#000000"] [--to-color "#ffffff"]

Examples::

    # Make a dark logo visible on the deck's dark background:
    python color_swap_svg.py logo.svg logo-light.svg \\
        --from-color "#000" --to-color "#fff"

    # Recolor an icon to the deck's accent color:
    python color_swap_svg.py icon.svg icon-accent.svg \\
        --from-color "#000" --to-color "#29b5e8"

If ``<output>`` is omitted the modified SVG is printed to stdout.
"""

import argparse
import re
import sys
from pathlib import Path

# Regex to validate hex color strings (3, 4, 6, or 8 hex digits).
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")

# Maps named colors to all their common hex/rgb representations so we can
# find and replace every variant in a single pass.
COLOR_ALIASES: dict[str, list[str]] = {
    "black": ["#000", "#000000", "rgb(0,0,0)", "rgb(0, 0, 0)"],
    "white": ["#fff", "#ffffff", "rgb(255,255,255)", "rgb(255, 255, 255)"],
}

# Quick lookup for expanding common shorthand hex codes to their full form.
HEX_EXPAND: dict[str, str] = {
    "#000": "#000000",
    "#fff": "#ffffff",
}

# Maximum SVG file size we'll process (10 MB).
MAX_SVG_SIZE_BYTES: int = 10 * 1024 * 1024


def validate_input(input_path: Path) -> None:
    """Validate that the input is an existing, readable SVG file.

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
            f"Error: Expected an .svg file, got '{input_path.suffix}'.",
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


def validate_color(color: str, label: str) -> None:
    """Check that a color argument looks like a valid CSS color value.

    Accepts hex colors, named colors in ``COLOR_ALIASES``, and ``rgb()``
    notation.  This is a best-effort check — not a full CSS parser.

    Args:
        color: The color string to validate.
        label: Human-readable label for error messages (e.g. ``"--from-color"``).

    Raises:
        SystemExit: If the color appears invalid.
    """
    c = color.strip().lower()

    # Accept known named colors.
    if c in COLOR_ALIASES:
        return

    # Accept hex colors.
    if c.startswith("#") and HEX_COLOR_RE.match(c):
        return

    # Accept rgb() notation (loose check).
    if c.startswith("rgb(") and c.endswith(")"):
        return

    print(
        f"Warning: {label} value '{color}' may not be a valid CSS color.  "
        f"Proceeding anyway — but results may be unexpected.",
        file=sys.stderr,
    )


def normalize_color(c: str) -> list[str]:
    """Expand a color value into all equivalent representations.

    Given a single color string (hex, shorthand, or named), returns a
    de-duplicated list of every variant that could appear in an SVG file.
    This lets ``swap_colors`` match regardless of how the editor serialized
    the color.

    Args:
        c: A CSS color value, e.g. ``"#000"``, ``"#000000"``, or ``"black"``.

    Returns:
        A list of lowercased color strings that are all visually identical.
    """
    c = c.strip().lower()
    variants = [c]

    # Add all aliases if this is a named color (e.g. "black" → #000, rgb(0,0,0), …).
    if c in COLOR_ALIASES:
        variants.extend(COLOR_ALIASES[c])

    # If we have a known shorthand, add its expanded form.
    expanded = HEX_EXPAND.get(c)
    if expanded:
        variants.append(expanded)

    # Expand shorthand hex (#abc → #aabbcc) or compress full hex (#aabbcc → #abc).
    if len(c) == 4 and c.startswith("#"):
        full = f"#{c[1]*2}{c[2]*2}{c[3]*2}"
        variants.append(full)
    elif len(c) == 7 and c.startswith("#"):
        # Only compressible if each pair of digits is identical (e.g. #112233 → #123).
        short = (
            f"#{c[1]}{c[3]}{c[5]}"
            if c[1] == c[2] and c[3] == c[4] and c[5] == c[6]
            else None
        )
        if short:
            variants.append(short)

    return list(set(v.lower() for v in variants))


def swap_colors(svg_content: str, from_color: str, to_color: str) -> str:
    """Replace all occurrences of ``from_color`` with ``to_color`` in SVG source.

    Targets three CSS/SVG properties:
        - ``fill`` (shape fill color)
        - ``stroke`` (outline color)
        - ``stop-color`` (gradient stop color)

    Each property is matched in both attribute (``fill="#000"``) and inline
    style (``fill:#000;``) contexts.

    If a regex substitution fails for a particular variant, that variant
    is skipped with a warning rather than aborting the entire operation.

    Args:
        svg_content: Raw SVG source text.
        from_color: The color to find (any supported format).
        to_color: The replacement color value.

    Returns:
        The modified SVG source with colors swapped.
    """
    # Build the full set of equivalent representations for the source color.
    from_variants = normalize_color(from_color)
    count = 0

    # Property names to target for color replacement.
    properties = ["fill", "stroke", "stop-color"]

    # Pre-compile all (variant × property) patterns before iterating.
    compiled: list[tuple[re.Pattern, str]] = []
    for variant in from_variants:
        escaped = re.escape(variant)
        for prop in properties:
            try:
                compiled.append((
                    re.compile(
                        rf'({re.escape(prop)}\s*[:=]\s*["\']?){escaped}(["\']?\s*[;\}}]?)',
                        re.IGNORECASE,
                    ),
                    prop,
                ))
            except re.error as exc:
                print(
                    f"Warning: Regex failed for {prop}='{variant}': {exc}",
                    file=sys.stderr,
                )

    for pattern, _prop in compiled:
        try:
            svg_content, n = pattern.subn(rf'\g<1>{to_color}\2', svg_content)
            count += n
        except re.error as exc:
            print(
                f"Warning: Substitution failed for pattern '{pattern.pattern[:40]}': {exc}",
                file=sys.stderr,
            )

    if count == 0:
        print(
            f"Warning: No occurrences of '{from_color}' found in the SVG.  "
            f"The file was not modified.  Check that the color value is correct.",
            file=sys.stderr,
        )
    else:
        print(
            f"# Replaced {count} color occurrence(s): {from_color} → {to_color}",
            file=sys.stderr,
        )

    return svg_content


def main() -> None:
    """Parse CLI arguments, perform the color swap, and write or print the result."""
    parser = argparse.ArgumentParser(
        description="Swap colors in an SVG for dark-background compatibility."
    )
    parser.add_argument("input", help="Path to the source SVG")
    parser.add_argument(
        "output", nargs="?", help="Output path (omit to print to stdout)"
    )
    parser.add_argument(
        "--from-color",
        default="#000000",
        help='Color to replace (default: "#000000")',
    )
    parser.add_argument(
        "--to-color",
        default="#ffffff",
        help='Replacement color (default: "#ffffff")',
    )
    args = parser.parse_args()

    p = Path(args.input)
    validate_input(p)
    validate_color(args.from_color, "--from-color")
    validate_color(args.to_color, "--to-color")

    # Read the SVG source.
    try:
        svg = p.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(
            f"Error: '{p}' contains invalid UTF-8: {exc}.  "
            f"SVG files must be valid UTF-8 or ASCII.",
            file=sys.stderr,
        )
        sys.exit(1)
    except OSError as exc:
        print(f"Error: Could not read '{p}': {exc}", file=sys.stderr)
        sys.exit(1)

    # Basic sanity check — make sure it's actually SVG.
    if "<svg" not in svg.lower():
        print(
            f"Error: '{p}' does not appear to contain SVG content "
            f"(no <svg> tag found).",
            file=sys.stderr,
        )
        sys.exit(1)

    result = swap_colors(svg, args.from_color, args.to_color)

    # Verify the result still has the <svg> tag — guard against catastrophic
    # regex damage.
    if "<svg" not in result.lower():
        print(
            "Warning: Color swap damaged the SVG structure.  "
            "Falling back to the original unmodified SVG.",
            file=sys.stderr,
        )
        result = svg

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
            output_path.write_text(result, encoding="utf-8")
        except OSError as exc:
            print(f"Error: Could not write to '{output_path}': {exc}", file=sys.stderr)
            sys.exit(1)

        print(f"# Saved to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
