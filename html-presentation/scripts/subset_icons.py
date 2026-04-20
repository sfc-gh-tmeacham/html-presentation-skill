#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Optimise the Material Symbols font link in a finished deck.

Scans the HTML file for every ``material-symbols-rounded`` icon name, then
rewrites the Google Fonts ``<link>`` to request only those icons using the
``&icon_names=`` subsetting parameter.  This reduces the font payload from
~295 KB (full set) to ~1–3 KB (used icons only).

Usage::

    python run_script.py subset_icons.py <deck.html>

The file is modified in-place.  Run after the deck is fully built (all slides
inserted, all images embedded) so the icon scan is complete.

Exit codes:

- 0: success (or nothing to do)
- 1: error — see stderr for details
"""

import re
import sys
from pathlib import Path


ICON_SPAN_RE = re.compile(
    r'<span[^>]*class="material-symbols-rounded"[^>]*>\s*([a-z_]+)\s*</span>',
    re.IGNORECASE,
)

FONT_LINK_RE = re.compile(
    r'<link\b[^>]*fonts\.googleapis\.com/css2\?family=Material\+Symbols\+Rounded[^>]*>',
    re.IGNORECASE,
)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python run_script.py subset_icons.py <deck.html>", file=sys.stderr)
        return 1

    deck_path = Path(sys.argv[1])
    if not deck_path.is_file():
        print(f"ERROR: file not found: {deck_path}", file=sys.stderr)
        return 1

    html = deck_path.read_text(encoding="utf-8")

    if not FONT_LINK_RE.search(html):
        print("INFO: no Material Symbols Rounded <link> found — nothing to do.")
        return 0

    icon_names = sorted(set(m.group(1).lower() for m in ICON_SPAN_RE.finditer(html)))

    if not icon_names:
        print("INFO: no material-symbols-rounded icons found in deck — nothing to subset.")
        return 0

    names_param = ",".join(icon_names)
    new_link = (
        f'<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded'
        f'&icon_names={names_param}&display=block" rel="stylesheet">'
    )

    new_html = FONT_LINK_RE.sub(new_link, html)
    deck_path.write_text(new_html, encoding="utf-8")

    print(f"SUCCESS: subsetted font to {len(icon_names)} icon(s): {', '.join(icon_names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
