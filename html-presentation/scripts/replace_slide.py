#!/usr/bin/env python3
"""Replace a fully-built slide in a deck by slide number.

Finds the ``<div id="sN" class="slide">...</div>`` block in the target deck
and replaces it with the matching block from a draft HTML file.  Useful when
a slide has already been inserted (no ``<!-- INSERT_SLIDE_N -->`` marker
remains) and needs to be rebuilt in-place.

Usage::

    python run_script.py replace_slide.py <deck.html> <draft.html> <slide_number>

Arguments:

- ``deck.html``     — the fully-built destination deck to modify in-place
- ``draft.html``    — a single-slide (or full-deck) HTML file containing the
  replacement slide with the same ``id="sN"``
- ``slide_number``  — integer slide number (e.g. ``7`` for ``id="s7"``)

Exit codes:

- 0: replacement succeeded
- 1: error — see stderr for details
"""

import re
import sys
from pathlib import Path


def find_slide_bounds(html: str, slide_id: str) -> tuple[int, int]:
    """Return the (start, end) byte offsets of ``<div id="sN" class="slide">...</div>``.

    Handles both attribute orderings (id-first and class-first).  Uses
    depth-tracking to find the exact closing ``</div>`` rather than a greedy
    regex, so nested ``<div>`` elements inside the slide do not confuse it.

    Args:
        html:      Full HTML string to search.
        slide_id:  The ``id`` value to locate, e.g. ``"s7"``.

    Returns:
        ``(start, end)`` character offsets where ``html[start:end]`` is the
        complete slide block, or ``(-1, -1)`` if not found.
    """
    escaped = re.escape(slide_id)
    pattern = re.compile(
        rf'<div\b(?=[^>]*\bid="{escaped}"[^>]*>)(?=[^>]*\bclass="slide\b)',
        re.IGNORECASE,
    )
    m = pattern.search(html)
    if not m:
        pattern2 = re.compile(
            rf'<div\b(?=[^>]*\bclass="slide\b[^>]*>)(?=[^>]*\bid="{escaped}")',
            re.IGNORECASE,
        )
        m = pattern2.search(html)
    if not m:
        return (-1, -1)

    pos = m.start()
    depth = 0
    i = pos
    length = len(html)
    while i < length:
        if html[i : i + 6] == "</div>":
            depth -= 1
            if depth == 0:
                return (pos, i + 6)
            i += 6
        elif html[i : i + 4] == "<div":
            depth += 1
            i += 4
        else:
            i += 1

    return (-1, -1)


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: python run_script.py replace_slide.py <deck.html> <draft.html> <slide_number>",
            file=sys.stderr,
        )
        return 1

    deck_path = Path(sys.argv[1])
    draft_path = Path(sys.argv[2])
    try:
        slide_num = int(sys.argv[3])
    except ValueError:
        print(f"ERROR: slide_number must be an integer, got '{sys.argv[3]}'", file=sys.stderr)
        return 1

    slide_id = f"s{slide_num}"

    if not deck_path.is_file():
        print(f"ERROR: deck file not found: {deck_path}", file=sys.stderr)
        return 1
    if not draft_path.is_file():
        print(f"ERROR: draft file not found: {draft_path}", file=sys.stderr)
        return 1

    deck_html = deck_path.read_text(encoding="utf-8")
    draft_html = draft_path.read_text(encoding="utf-8")

    draft_start, draft_end = find_slide_bounds(draft_html, slide_id)
    if draft_start == -1:
        print(
            f"ERROR: slide '{slide_id}' not found in draft file: {draft_path}",
            file=sys.stderr,
        )
        return 1

    replacement = draft_html[draft_start:draft_end]

    deck_start, deck_end = find_slide_bounds(deck_html, slide_id)
    if deck_start == -1:
        print(
            f"ERROR: slide '{slide_id}' not found in deck file: {deck_path}",
            file=sys.stderr,
        )
        return 1

    new_html = deck_html[:deck_start] + replacement + deck_html[deck_end:]
    deck_path.write_text(new_html, encoding="utf-8")

    print(f"SUCCESS: replaced slide {slide_num} in {deck_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
