#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "Pillow>=9.0",
# ]
# ///
"""
svg_calc.py — SVG coordinate calculator for HTML presentations

Eliminates the three most common SVG layout bugs:
  1. Overlapping stacked rects (wrong y values)
  2. viewBox too short (content clipped silently)
  3. Box too narrow for label text (text overflows)

Usage via run_script.py:
  python scripts/run_script.py svg_calc.py <command> [options]

Commands:
  stack       Compute y positions for N vertically-stacked boxes
  textbox     Estimate minimum rect width for a given text label
  distribute  Compute x centers for N columns evenly across a viewBox width
  grid        Full x/y coordinate table for a multi-column, multi-row diagram
  viewbox     Compute required viewBox height given a list of y:height pairs
  arrow       Generate SVG path `d` for a vertical connector arrow between two boxes
  layout      JSON-driven full layout (boxes + arrows + viewBox) for flow diagrams
  marker      Compute SVG marker dimensions for a given arrow gap size
  audit       Audit an existing viewBox for wasted space and bad aspect ratio

Run any command with --help for details.
"""

import sys
import argparse
import json
import math

try:
    from PIL import ImageFont as _ImageFont
    _HAVE_PILLOW = True
except ImportError:
    _HAVE_PILLOW = False

_FONT_PATHS = [
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

_BOLD_FONT_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

_font_cache: dict = {}


def _load_font(font_size: int, bold: bool = False):
    """Return a PIL ImageFont for the given size, or None if unavailable."""
    if not _HAVE_PILLOW:
        return None
    key = (font_size, bold)
    if key in _font_cache:
        return _font_cache[key]
    paths = _BOLD_FONT_PATHS + _FONT_PATHS if bold else _FONT_PATHS
    for path in paths:
        try:
            font = _ImageFont.truetype(path, font_size)
            _font_cache[key] = font
            return font
        except (OSError, IOError):
            continue
    _font_cache[key] = None
    return None


_CHAR_WIDTH_TABLE = {
    'i': 0.31, 'l': 0.31, '1': 0.40, 'j': 0.33, 'r': 0.39, 't': 0.38,
    'f': 0.38, 'I': 0.36, '|': 0.27, '!': 0.36, ':': 0.36, ';': 0.36,
    ',': 0.36, '.': 0.36, ' ': 0.30,
    'W': 0.88, 'M': 0.83, 'm': 0.83, 'w': 0.79, 'O': 0.74, 'Q': 0.74,
    'G': 0.72, 'C': 0.67, 'D': 0.72, 'H': 0.72, 'N': 0.72, 'U': 0.67,
    '@': 0.85, '%': 0.72,
}
_DEFAULT_CHAR_WIDTH = 0.57

_SAFETY_BUFFER = 5


def estimate_text_width(text: str, font_size: int = 12, bold: bool = False) -> int:
    """Return estimated pixel width of `text` at `font_size`.

    Uses Pillow (PIL.ImageFont) with a system font when available for
    per-glyph accuracy.  Falls back to a per-character width table when no
    system font can be loaded.
    """
    font = _load_font(font_size, bold=bold)
    if font is not None:
        bbox = font.getbbox(text)
        return (bbox[2] - bbox[0]) + _SAFETY_BUFFER
    raw = sum(_CHAR_WIDTH_TABLE.get(c, _DEFAULT_CHAR_WIDTH) for c in text) * font_size
    if bold:
        raw *= 1.15
    return math.ceil(raw)


def _measurement_method() -> str:
    """Return a short label describing which measurement path is active."""
    if _load_font(12) is not None:
        return "Pillow/font"
    if _HAVE_PILLOW:
        return "per-char table (no system font found)"
    return "per-char table (Pillow not available)"


# ---------------------------------------------------------------------------
# stack
# ---------------------------------------------------------------------------
def cmd_stack(args):
    """
    Compute y positions for N vertically-stacked boxes of uniform height.

    Options:
      --count N        Number of boxes (required)
      --box-height H   Height of each box in px (required)
      --gap G          Gap between boxes in px (default 12)
      --start-y Y      y of the first box (default 20)
      --box-width W    Width of each box — used for overlap validation (optional)
      --labels L       Comma-separated labels — validates each fits in W (optional)
    """
    p = argparse.ArgumentParser(prog="svg_calc.py stack")
    p.add_argument("--count",        "-n", type=int,   required=True)
    p.add_argument("--box-height",   "-H", type=int,   required=True)
    p.add_argument("--gap",          "-g", type=int,   default=12)
    p.add_argument("--start-y",      "-y", type=int,   default=20)
    p.add_argument("--box-width",    "-W", type=int,   default=None)
    p.add_argument("--font-size",    "-f", type=int,   default=12)
    p.add_argument("--bold",               action="store_true", default=False,
                   help="Treat labels as bold text for width estimation")
    p.add_argument("--labels",       "-l", type=str,   default=None)
    p.add_argument("--container-y",  "-c", type=int,   default=None,
                   help="y of the outer container rect — outputs required container height")
    a = p.parse_args(args)

    labels = [s.strip() for s in a.labels.split(",")] if a.labels else []
    if labels and len(labels) != a.count:
        print(f"WARNING: --labels has {len(labels)} items but --count is {a.count}. Labels ignored.")
        labels = []

    print(f"\nStack layout: {a.count} boxes × {a.box_height}px, gap={a.gap}px, start-y={a.start_y}\n")
    print(f"{'Box':<5} {'y':>6} {'bottom (y+h)':>14}  {'label'}")
    print("-" * 55)

    ys = []
    warnings = []
    for i in range(a.count):
        y = a.start_y + i * (a.box_height + a.gap)
        bottom = y + a.box_height
        ys.append(y)
        label = labels[i] if labels else ""

        # Check text width vs box width
        width_warn = ""
        if label and a.box_width:
            h_pad = 24
            min_w = estimate_text_width(label, a.font_size, bold=a.bold) + h_pad
            if min_w > a.box_width:
                width_warn = f"  ⚠ TEXT MAY CLIP: need ~{min_w}px, have {a.box_width}px"
                warnings.append(f"Box {i}: '{label}' needs ~{min_w}px width")

        print(f"  {i:<3} {y:>6}   {bottom:>14}  {label}{width_warn}")

    last_bottom = ys[-1] + a.box_height
    viewbox_h = last_bottom + 20

    print(f"\nviewBox height required : {viewbox_h}  (last bottom {last_bottom} + 20px margin)")

    if a.container_y is not None:
        container_h = last_bottom + 8 - a.container_y
        print(f"container rect height   : {container_h}  "
              f"(last bottom {last_bottom} + 8px padding - container_y {a.container_y})"
              f"\n  ➜  <rect y=\"{a.container_y}\" height=\"{container_h}\" ...>")

    if warnings:
        print(f"\n{'─'*55}")
        print("Text width warnings:")
        for w in warnings:
            print(f"  ⚠  {w}")

    print(f"\nPaste-ready y values: {ys}")
    print()


# ---------------------------------------------------------------------------
# textbox
# ---------------------------------------------------------------------------
def cmd_textbox(args):
    """
    Estimate the minimum rect width for one or more text labels.

    Options:
      --text T         Label string (required; repeat for multiple)
      --font-size F    Font size in SVG units (default 12)
      --padding P      Total horizontal padding in px (default 24)
    """
    p = argparse.ArgumentParser(prog="svg_calc.py textbox")
    p.add_argument("--text",      "-t", type=str,  action="append", required=True)
    p.add_argument("--font-size", "-f", type=int,  default=12)
    p.add_argument("--padding",   "-p", type=int,  default=24)
    p.add_argument("--bold",            action="store_true", default=False,
                   help="Estimate for bold text (uses bold font or 1.15x multiplier)")
    a = p.parse_args(args)

    method = _measurement_method()
    bold_tag = " bold" if a.bold else ""
    print(f"\nText width estimates (font-size={a.font_size}{bold_tag}, h-padding={a.padding}, method={method})\n")
    print(f"{'Label':<45} {'text_px':>8}  {'min_rect_w':>10}")
    print("-" * 68)
    max_w = 0
    for text in a.text:
        tw = estimate_text_width(text, a.font_size, bold=a.bold)
        min_w = tw + a.padding
        max_w = max(max_w, min_w)
        print(f"  {text:<43} {tw:>8}  {min_w:>10}")
    print(f"\n  ➜  Recommended box width (widest label): {max_w}px")
    print()


# ---------------------------------------------------------------------------
# distribute
# ---------------------------------------------------------------------------
def cmd_distribute(args):
    """
    Compute x centers and column width for N evenly-distributed columns.

    Options:
      --width  W    viewBox width (required)
      --margin M    Left AND right margin in px (default 30)
      --count  N    Number of columns (required)
      --gap    G    Gap between columns (default 16). When set, ignores equal spacing.
    """
    p = argparse.ArgumentParser(prog="svg_calc.py distribute")
    p.add_argument("--width",  "-W", type=int, required=True)
    p.add_argument("--margin", "-m", type=int, default=30)
    p.add_argument("--count",  "-n", type=int, required=True)
    p.add_argument("--gap",    "-g", type=int, default=None)
    a = p.parse_args(args)

    usable = a.width - 2 * a.margin

    if a.gap is not None:
        col_w = (usable - a.gap * (a.count - 1)) / a.count
    else:
        col_w = usable / a.count
        a.gap = 0

    print(f"\nDistribute {a.count} columns in viewBox width={a.width}, margin={a.margin}, gap={a.gap}\n")
    print(f"  Usable width  : {usable}px")
    print(f"  Column width  : {col_w:.1f}px\n")

    centers = []
    print(f"  {'Col':<5} {'x_left':>8}  {'cx (center)':>12}  {'x_right':>9}")
    print("  " + "-" * 42)
    for i in range(a.count):
        x_left = a.margin + i * (col_w + a.gap)
        cx = x_left + col_w / 2
        x_right = x_left + col_w
        centers.append(round(cx, 1))
        print(f"  {i:<5} {x_left:>8.1f}  {cx:>12.1f}  {x_right:>9.1f}")

    print(f"\n  ➜  cx values: {centers}")
    print()


# ---------------------------------------------------------------------------
# viewbox
# ---------------------------------------------------------------------------
def cmd_viewbox(args):
    """
    Compute the required viewBox height given elements defined as y:height pairs.

    Options:
      --elements E    Comma-separated "y:height" pairs, e.g. "20:48,84:48,148:60"
      --margin M      Bottom margin to add (default 20)
    """
    p = argparse.ArgumentParser(prog="svg_calc.py viewbox")
    p.add_argument("--elements", "-e", type=str, required=True,
                   help='Comma-separated y:height pairs, e.g. "20:48,84:48"')
    p.add_argument("--width",    "-W", type=int, default=None)
    p.add_argument("--margin",   "-m", type=int, default=20)
    a = p.parse_args(args)

    pairs = []
    for token in a.elements.split(","):
        token = token.strip()
        if ":" not in token:
            print(f"ERROR: malformed element '{token}' — expected y:height")
            sys.exit(1)
        y_str, h_str = token.split(":", 1)
        pairs.append((int(y_str), int(h_str)))

    max_bottom = max(y + h for y, h in pairs)
    required_h = max_bottom + a.margin

    print(f"\nviewBox height check\n")
    print(f"  {'y':>6}  {'height':>8}  {'bottom':>8}  {'clips?':>8}")
    print("  " + "-" * 40)
    for y, h in pairs:
        bottom = y + h
        clips = "⚠ CLIPS" if bottom > (required_h - a.margin) and bottom == max_bottom else ""
        print(f"  {y:>6}  {h:>8}  {bottom:>8}  {clips}")

    width_str = f"{a.width} " if a.width else "W "
    print(f"\n  ➜  viewBox=\"0 0 {width_str}{required_h}\"  (max_bottom={max_bottom} + {a.margin}px margin)")
    print()


# ---------------------------------------------------------------------------
# arrow
# ---------------------------------------------------------------------------
def cmd_arrow(args):
    """
    Generate SVG path `d` attribute for a straight vertical connector arrow.

    The arrow starts at the bottom-center of the source box and ends at the
    top-center of the target box, with an optional arrowhead marker reference.

    Options:
      --cx X        Horizontal center x (shared for both boxes) (required)
      --from-y Y    Bottom edge of the source box (required)
      --to-y Y      Top edge of the target box (required)
    """
    p = argparse.ArgumentParser(prog="svg_calc.py arrow")
    p.add_argument("--cx",     "-x", type=float, required=True)
    p.add_argument("--from-y", "-a", type=float, required=True, dest="from_y")
    p.add_argument("--to-y",   "-b", type=float, required=True, dest="to_y")
    a = p.parse_args(args)

    gap = a.to_y - a.from_y
    if gap <= 0:
        print(f"ERROR: --to-y ({a.to_y}) must be greater than --from-y ({a.from_y})")
        sys.exit(1)

    mid_y = (a.from_y + a.to_y) / 2

    print(f"\nVertical connector arrow\n")
    print(f"  cx={a.cx}  from_y={a.from_y}  to_y={a.to_y}  gap={gap}px\n")
    print(f'  Straight line path:')
    print(f'    d="M{a.cx},{a.from_y} L{a.cx},{a.to_y}"')
    print(f'\n  With mid-point (for styling):')
    print(f'    d="M{a.cx},{a.from_y} L{a.cx},{mid_y} L{a.cx},{a.to_y}"')
    print(f'\n  Inline SVG line element:')
    print(f'    <line x1="{a.cx}" y1="{a.from_y}" x2="{a.cx}" y2="{a.to_y}" '
          f'stroke="var(--accent)" stroke-width="2" marker-end="url(#arrow)"/>')
    print()


# ---------------------------------------------------------------------------
# grid
# ---------------------------------------------------------------------------
def cmd_grid(args):
    """
    Generate a complete x/y coordinate table for a multi-column, multi-row SVG layout.

    Options:
      --cols C          Number of columns (required)
      --rows R          Number of rows (required)
      --box-width W     Width of each box (required)
      --box-height H    Height of each box (required)
      --col-gap G       Horizontal gap between columns (default 24)
      --row-gap G       Vertical gap between rows (default 16)
      --margin-x M      Left/right margin (default 30)
      --margin-y M      Top margin (default 20)
      --viewbox-width V Total viewBox width (default: computed from cols)
    """
    p = argparse.ArgumentParser(prog="svg_calc.py grid")
    p.add_argument("--cols",          "-c", type=int, required=True)
    p.add_argument("--rows",          "-r", type=int, required=True)
    p.add_argument("--box-width",     "-W", type=int, required=True)
    p.add_argument("--box-height",    "-H", type=int, required=True)
    p.add_argument("--col-gap",             type=int, default=24)
    p.add_argument("--row-gap",             type=int, default=16)
    p.add_argument("--margin-x",            type=int, default=30)
    p.add_argument("--margin-y",            type=int, default=20)
    p.add_argument("--viewbox-width", "-V", type=int, default=None)
    a = p.parse_args(args)

    vb_w = a.viewbox_width or (a.margin_x * 2 + a.cols * a.box_width + (a.cols - 1) * a.col_gap)
    vb_h = a.margin_y + a.rows * a.box_height + (a.rows - 1) * a.row_gap + 20

    print(f"\nGrid layout: {a.cols}×{a.rows}  box={a.box_width}×{a.box_height}  "
          f"col-gap={a.col_gap}  row-gap={a.row_gap}\n")
    print(f"  viewBox=\"0 0 {vb_w} {vb_h}\"\n")
    print(f"  {'Cell':<10} {'x':>6} {'y':>6} {'cx':>8} {'cy':>8} {'right':>8} {'bottom':>8}")
    print("  " + "-" * 58)

    for row in range(a.rows):
        for col in range(a.cols):
            x = a.margin_x + col * (a.box_width + a.col_gap)
            y = a.margin_y + row * (a.box_height + a.row_gap)
            cx = x + a.box_width // 2
            cy = y + a.box_height // 2
            right = x + a.box_width
            bottom = y + a.box_height
            cell = f"[{row},{col}]"
            print(f"  {cell:<10} {x:>6} {y:>6} {cx:>8} {cy:>8} {right:>8} {bottom:>8}")
        if row < a.rows - 1:
            print()

    print(f"\n  ➜  viewBox: 0 0 {vb_w} {vb_h}")
    print()


# ---------------------------------------------------------------------------
# layout (JSON-driven)
# ---------------------------------------------------------------------------
def cmd_layout(args):
    """
    Full coordinate layout for a vertical flow diagram from a JSON spec.

    JSON format (file or --inline):
    {
      "viewbox_width": 300,
      "box_width": 220,
      "box_height": 48,
      "gap": 16,
      "start_y": 20,
      "font_size": 12,
      "boxes": [
        {"label": "ACCOUNT_USAGE"},
        {"label": "Filter: last 30d", "sublabel": "WHERE ..."},
        {"label": "GROUP BY warehouse_name"},
        {"label": "Sum credits", "highlight": true}
      ]
    }

    Options:
      --file F      Path to JSON spec file (required unless --inline)
      --inline J    JSON string inline
    """
    p = argparse.ArgumentParser(prog="svg_calc.py layout")
    p.add_argument("--file",   "-f", type=str, default=None)
    p.add_argument("--inline", "-i", type=str, default=None)
    a = p.parse_args(args)

    if a.file:
        with open(a.file) as fh:
            spec = json.load(fh)
    elif a.inline:
        spec = json.loads(a.inline)
    else:
        p.print_help()
        sys.exit(1)

    vb_w    = spec.get("viewbox_width", 300)
    box_w   = spec.get("box_width",     220)
    box_h   = spec.get("box_height",     48)
    gap     = spec.get("gap",            16)
    start_y = spec.get("start_y",        20)
    fs      = spec.get("font_size",      12)
    boxes   = spec.get("boxes",          [])

    cx = vb_w // 2
    h_pad = 24

    print(f"\nFlow diagram layout: {len(boxes)} boxes, viewBox width={vb_w}\n")
    print(f"  {'#':<4} {'y':>5} {'bottom':>8}  {'cx':>5}  {'min_w':>7}  {'ok?':>5}  label")
    print("  " + "-" * 68)

    warnings = []
    elements = []
    for i, box in enumerate(boxes):
        label = box.get("label", f"Box {i}")
        y = start_y + i * (box_h + gap)
        bottom = y + box_h
        min_w = estimate_text_width(label, fs) + h_pad
        ok = "✓" if box_w >= min_w else f"⚠ need {min_w}"
        elements.append((y, box_h))
        print(f"  {i:<4} {y:>5} {bottom:>8}  {cx:>5}  {min_w:>7}  {ok:>5}  {label}")
        if box_w < min_w:
            warnings.append(f"Box {i} '{label}': box_width {box_w} < min {min_w}")

    print()

    last_y, last_h = elements[-1]
    vb_h = last_y + last_h + 20
    print(f"  viewBox = \"0 0 {vb_w} {vb_h}\"")
    print()

    print("  Connector arrows (x1=cx, y1=box_bottom, x2=cx, y2=next_box_top):")
    for i in range(len(elements) - 1):
        y_from = elements[i][0] + elements[i][1]
        y_to   = elements[i + 1][0]
        print(f'    <line x1="{cx}" y1="{y_from}" x2="{cx}" y2="{y_to}" '
              f'stroke="var(--accent)" stroke-width="2" marker-end="url(#arrow)"/>')

    if warnings:
        print(f"\n  ⚠  Width warnings:")
        for w in warnings:
            print(f"     {w}")

    print()


# ---------------------------------------------------------------------------
# marker
# ---------------------------------------------------------------------------
def cmd_marker(args):
    p = argparse.ArgumentParser(prog="svg_calc.py marker")
    p.add_argument("--gap",          "-g", type=float, required=True,
                   help="Gap in px between source bottom and target top")
    p.add_argument("--stroke-width", "-s", type=float, default=2.0,
                   help="Stroke width of the connector line (default 2)")
    p.add_argument("--ratio",        "-r", type=float, default=0.7,
                   help="Fraction of the gap the marker should occupy (default 0.7)")
    a = p.parse_args(args)

    marker_h = round(a.gap * a.ratio, 1)
    marker_w = round(marker_h * 1.43, 1)
    ref_x = marker_w
    ref_y = round(marker_h / 2, 1)

    bad_h = marker_h * a.stroke_width
    bad_w = marker_w * a.stroke_width

    print(f"\nMarker sizing for gap={a.gap}px, stroke-width={a.stroke_width}, ratio={a.ratio}\n")
    print(f"  markerUnits    : userSpaceOnUse  (REQUIRED — prevents stroke-width scaling)")
    print(f"  markerWidth    : {marker_w}")
    print(f"  markerHeight   : {marker_h}")
    print(f"  refX           : {ref_x}")
    print(f"  refY           : {ref_y}")
    print(f"\n  Without userSpaceOnUse (BAD): effective {bad_w} x {bad_h} — "
          f"{'OVERFLOWS gap' if bad_h > a.gap else 'fits but oversized'}")

    if a.gap < 14:
        print(f"\n  WARNING: gap {a.gap}px is below 14px minimum — increase gap between elements")

    print(f'\n  Paste-ready:\n')
    print(f'  <defs>')
    print(f'    <marker id="arrN" markerWidth="{marker_w}" markerHeight="{marker_h}" '
          f'refX="{ref_x}" refY="{ref_y}" orient="auto" markerUnits="userSpaceOnUse">')
    print(f'      <polygon points="0 0, {marker_w} {ref_y}, 0 {marker_h}" fill="var(--accent)"/>')
    print(f'    </marker>')
    print(f'  </defs>')
    print()


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------
def cmd_audit(args):
    p = argparse.ArgumentParser(prog="svg_calc.py audit")
    p.add_argument("--viewbox", "-v", type=str, required=True,
                   help='viewBox value, e.g. "0 0 800 300"')
    p.add_argument("--elements", "-e", type=str, required=True,
                   help='Comma-separated y:height pairs of all content elements')
    a = p.parse_args(args)

    vb_parts = a.viewbox.split()
    if len(vb_parts) != 4:
        print("ERROR: viewBox must have 4 values (min-x min-y width height)")
        sys.exit(1)
    vb_x, vb_y, vb_w, vb_h = (float(v) for v in vb_parts)

    pairs = []
    for token in a.elements.split(","):
        token = token.strip()
        if ":" not in token:
            print(f"ERROR: malformed element '{token}' -- expected y:height")
            sys.exit(1)
        y_str, h_str = token.split(":", 1)
        pairs.append((float(y_str), float(h_str)))

    min_y = min(y for y, h in pairs)
    max_bottom = max(y + h for y, h in pairs)
    top_gap = (min_y - vb_y) / vb_h * 100 if vb_h > 0 else 0
    bottom_gap = ((vb_y + vb_h) - max_bottom) / vb_h * 100 if vb_h > 0 else 0
    ratio = vb_w / vb_h if vb_h > 0 else 0
    ideal_h = max_bottom + 20

    print(f"\nviewBox audit: {vb_x:.0f} {vb_y:.0f} {vb_w:.0f} {vb_h:.0f}\n")
    print(f"  Content y range : {min_y:.0f} to {max_bottom:.0f} ({max_bottom - min_y:.0f}px)")
    print(f"  Top gap         : {top_gap:.0f}% {'FAIL (>12%)' if top_gap > 12 else 'OK'}")
    print(f"  Bottom gap      : {bottom_gap:.0f}% {'FAIL (>12%)' if bottom_gap > 12 else 'OK'}")
    print(f"  Aspect ratio    : {ratio:.2f}:1 {'FAIL (>2.5:1)' if ratio > 2.5 else 'OK'}")
    print(f"  Ideal viewBox h : {ideal_h:.0f} (content + 20px margin)")
    if ratio > 2.5:
        min_h = round(vb_w / 2.5)
        print(f"  Min height for ratio: {min_h} (to get 2.5:1)")
    print()


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
COMMANDS = {
    "stack":      cmd_stack,
    "textbox":    cmd_textbox,
    "distribute": cmd_distribute,
    "viewbox":    cmd_viewbox,
    "arrow":      cmd_arrow,
    "grid":       cmd_grid,
    "layout":     cmd_layout,
    "marker":     cmd_marker,
    "audit":      cmd_audit,
}

USAGE = """\
svg_calc.py — SVG coordinate calculator

Commands:
  stack       y positions for N stacked boxes
  textbox     minimum rect width for a text label
  distribute  x centers for N columns across a viewBox width
  grid        full x/y table for a multi-column, multi-row diagram
  viewbox     required viewBox height from y:height element pairs
  arrow       SVG path d for a vertical connector arrow
  layout      full flow diagram coordinates from a JSON spec
  marker      compute marker dimensions for a given arrow gap
  audit       audit an existing viewBox for wasted space and bad ratio

Examples:
  python scripts/run_script.py svg_calc.py stack --count 5 --box-height 48 --gap 12
  python scripts/run_script.py svg_calc.py textbox --text "WAREHOUSE_METERING_HISTORY" --font-size 12
  python scripts/run_script.py svg_calc.py textbox --text "Bold Label Here" --font-size 12 --bold
  python scripts/run_script.py svg_calc.py distribute --width 720 --margin 30 --count 4
  python scripts/run_script.py svg_calc.py viewbox --elements "20:48,84:48,148:60" --width 300
  python scripts/run_script.py svg_calc.py arrow --cx 150 --from-y 68 --to-y 84
  python scripts/run_script.py svg_calc.py grid --cols 3 --rows 2 --box-width 180 --box-height 48
  python scripts/run_script.py svg_calc.py layout --inline '{"viewbox_width":300,"box_width":220,"box_height":48,"gap":16,"start_y":20,"boxes":[{"label":"Source table"},{"label":"Filter rows"},{"label":"Aggregate"}]}'
  python scripts/run_script.py svg_calc.py marker --gap 16 --stroke-width 2
  python scripts/run_script.py svg_calc.py audit --viewbox "0 0 800 300" --elements "30:45,90:45,150:45,60:175,100:35,145:35,190:35"
"""

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(USAGE)
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd not in COMMANDS:
        print(f"Unknown command: '{cmd}'\n")
        print(USAGE)
        sys.exit(1)

    COMMANDS[cmd](sys.argv[2:])
