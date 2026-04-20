#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""
insert_slide.py — insert a subagent-generated slide draft into the HTML shell.

Reads a draft file written by a slide subagent, extracts the
<div id="sN" class="slide">...</div> block, validates the slide ID matches
the expected slide number, then replaces the <!-- INSERT_SLIDE_N --> marker
in the target deck file and writes the deck back.

This eliminates the need for the main agent to read large HTML content from
subagent return values — subagents write their output to a draft file, and
this script handles the extraction and insertion.

Usage (via run_script.py from html-presentation/):
  python scripts/run_script.py insert_slide.py \\
      <deck.html> <draft_file.html> <slide_number>

Arguments:
  deck.html        Path to the target deck HTML file (will be modified in-place)
  draft_file.html  Path to the subagent draft file (e.g. my-deck/drafts/slide_3.html)
  slide_number     Integer slide number N — must match id="sN" in the draft

Exit codes:
  0  success — marker replaced and deck written back
  1  error   — missing args, file not found, ID mismatch, marker absent, etc.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _fail(message: str, hint: str = "") -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(f"HINT:  {hint}", file=sys.stderr)
    return 1


SLIDE_BLOCK_RE = re.compile(
    r'(<div\s[^>]*\bid="s(\d+)"[^>]*class="slide"[^>]*>|<div\s[^>]*\bclass="slide"[^>]*\bid="s(\d+)"[^>]*>)'
    r'.*?'
    r'^</div>',
    re.DOTALL | re.MULTILINE,
)


def extract_slide_block(html: str, expected_n: int) -> tuple[str, int] | None:
    """Extract the outermost <div id="sN" class="slide">...</div> block.

    Walks the HTML character-by-character tracking open/close div depth
    starting from the first <div> that has both id="sN" and class="slide".
    Returns (block_html, slide_number) or None if not found.
    """
    open_tag_re = re.compile(
        r'<div\b[^>]*\bid="s(\d+)"[^>]*\bclass="(?:[^"]*\s)?slide(?:\s[^"]*)?"[^>]*>|'
        r'<div\b[^>]*\bclass="(?:[^"]*\s)?slide(?:\s[^"]*)?"[^>]*\bid="s(\d+)"[^>]*>',
        re.IGNORECASE,
    )

    match = open_tag_re.search(html)
    if not match:
        return None

    slide_n = int(match.group(1) or match.group(2))
    start = match.start()
    pos = match.end()
    depth = 1

    div_open = re.compile(r'<div\b', re.IGNORECASE)
    div_close = re.compile(r'</div\s*>', re.IGNORECASE)

    while depth > 0 and pos < len(html):
        next_open = div_open.search(html, pos)
        next_close = div_close.search(html, pos)

        if next_close is None:
            return None

        if next_open is not None and next_open.start() < next_close.start():
            depth += 1
            pos = next_open.end()
        else:
            depth -= 1
            pos = next_close.end()

    if depth != 0:
        return None

    return html[start:pos], slide_n


def main() -> int:
    if len(sys.argv) != 4:
        return _fail(
            f"Expected 3 arguments, got {len(sys.argv) - 1}",
            "Usage: python scripts/run_script.py insert_slide.py "
            "<deck.html> <draft_file.html> <slide_number>",
        )

    deck_path = Path(sys.argv[1])
    draft_path = Path(sys.argv[2])
    try:
        slide_n = int(sys.argv[3])
    except ValueError:
        return _fail(
            f"slide_number '{sys.argv[3]}' is not an integer",
            "Pass the slide number as a plain integer, e.g. 3",
        )

    if slide_n < 1:
        return _fail(
            f"slide_number {slide_n} is invalid; must be >= 1",
            "Slide numbers start at 1. Check your argument.",
        )

    if not deck_path.exists():
        return _fail(
            f"Deck file not found: {deck_path}",
            "Confirm the deck path is correct and generate_shell.py has already run.",
        )

    if not draft_path.exists():
        return _fail(
            f"Draft file not found: {draft_path}",
            f"Expected subagent to write slide {slide_n} to {draft_path}. "
            "Check that the subagent completed successfully.",
        )

    try:
        deck_html = deck_path.read_text(encoding="utf-8")
    except OSError as exc:
        return _fail(f"Could not read deck file: {exc}", "Check file permissions.")

    try:
        draft_html = draft_path.read_text(encoding="utf-8")
    except OSError as exc:
        return _fail(f"Could not read draft file: {exc}", "Check file permissions.")

    if not draft_html.strip():
        return _fail(
            f"Draft file {draft_path} is empty",
            f"Subagent may have failed to write slide {slide_n}. Re-run the subagent.",
        )

    result = extract_slide_block(draft_html, slide_n)
    if result is None:
        return _fail(
            f'No <div id="s{slide_n}" class="slide"> block found in {draft_path}',
            f'Verify the draft contains exactly one <div id="s{slide_n}" class="slide">. '
            "Check that the subagent followed the required output format.",
        )

    slide_block, found_n = result

    if found_n != slide_n:
        return _fail(
            f'Slide ID mismatch: expected s{slide_n} but draft contains s{found_n}',
            f"Subagent wrote slide {found_n} but this script was called for slide {slide_n}. "
            "Check subagent prompt and draft file path.",
        )

    marker = f"<!-- INSERT_SLIDE_{slide_n} -->"
    if marker not in deck_html:
        return _fail(
            f"Marker '{marker}' not found in {deck_path}",
            f"Slide {slide_n} may have already been inserted, or the marker was "
            "removed. Grep the deck for INSERT_SLIDE to check remaining markers.",
        )

    updated_html = deck_html.replace(marker, slide_block, 1)

    try:
        deck_path.write_text(updated_html, encoding="utf-8")
    except OSError as exc:
        return _fail(
            f"Could not write deck file: {exc}",
            f"Check that {deck_path} is writable.",
        )

    print(f"SUCCESS: Inserted slide {slide_n} → {deck_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
