#!/usr/bin/env python3
"""Validate a slide deck HTML file against the HTML Presentation skill rules.

Checks for common issues that can break navigation, visual quality, or
accessibility. Returns a pass/warn/fail summary with actionable messages.

Checks performed:

1. **Slide IDs** — sequential ``id="s1"``, ``s2``, ... with no gaps or dupes
2. **Total counter** — ``<span id="total">`` matches actual slide count
3. **Orphan placeholders** — leftover ``{{IMG:...}}`` tokens not yet embedded
4. **Visual component** — every slide has at least one visual element
   (card-grid, stat, step-flow, compare, metric, SVG, img, canvas, table, etc.)
5. **Word count** — flags slides exceeding 30 visible words
6. **Speaker notes** — if any slide has notes, all should (consistency)
7. **Accessibility** — ``<img>`` tags missing ``alt`` attribute
8. **Slide transitions** — warns if ``display:none`` is used instead of opacity
9. **Reduced motion** — checks for ``prefers-reduced-motion`` media query
10. **Material Icons** — verifies the correct stylesheet URL and class name
11. **Double bullets** — warns when ``<li>`` items use leading symbols/emojis
   but the parent ``<ul>`` is missing ``list-style: none``
12. **QR appendix** — warns when the deck has external links but no QR
   appendix slide; also warns if any appendix slide exceeds 6 QR codes
13. **Link attributes** — warns when ``<a>`` tags are missing
   ``target="_blank"`` or ``rel="noopener"`` (Rule 13)
14. **List alignment** — warns when ``<ul>``/``<ol>`` elements are missing
   ``text-align: left`` (Rule 12)
15. **SVG max-height** — warns when SVG containers use ``max-height`` below
   58vh, which causes empty bands on slides (Rule 16)
16. **Nav HTML structure** — fails if ``<span id="prev">``, ``<span id="next">``,
   ``<span id="curr">``, ``<span id="notes-hint">``, or ``class="nbtn"`` spans
   are absent; warns if ``<button>`` elements are found inside ``#nav``
17. **Notes panel HTML** — fails if ``id="notes-panel"``, ``id="notes-panel-text"``,
   or ``id="notes-panel-close"`` are missing (when speaker notes present)
18. **Notes CSS** — warns on each missing required rule: ``.speaker-notes``
   display:none, ``#deck.panel-open`` height calc, ``body.panel-open #nav``
   (when speaker notes present)
19. **JS wiring** — fails if legacy ``toggleNotes()`` found; warns if
   ``openNotesWindow``, ``openNotesPanel``, ``closeNotesPanel``, or N/B
   key bindings are absent (when speaker notes present)
20. **SVG text overflow** — warns when estimated text width
   (``len × font-size × 0.65``) exceeds the containing ``<rect>`` width
   by more than 20px; run ``svg_calc.py textbox`` to confirm and fix
21. **SVG viewBox top-gap** — warns when the first content element's ``y``
   position exceeds 12% of the viewBox height, creating a blank band at
   the top of the diagram
22. **SVG rect overflow** — warns when a ``<rect>`` element's bottom or
   right edge extends beyond its containing ``<rect>`` (inner box escaping
   its panel container); run ``svg_calc.py stack --container-y`` to fix

Usage::

    python run_script.py validate_deck.py <deck.html>

Exit codes:

- 0: all checks passed (may have warnings)
- 1: one or more checks failed
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_WORDS_PER_SLIDE = 30
MAX_QR_PER_SLIDE = 6
MIN_SVG_VH = 58
SVG_CHAR_WIDTH = 0.65
SVG_OVERFLOW_TOLERANCE = 20.0
SVG_GAP_THRESHOLD = 0.12

VISUAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r'class="[^"]*card-grid',
    r'class="[^"]*card["\s]',
    r'class="[^"]*stat-number',
    r'class="[^"]*stat-big',
    r'class="[^"]*stat-label',
    r'class="[^"]*step-flow',
    r'class="[^"]*compare["\s]',
    r'class="[^"]*comparison["\s]',
    r'class="[^"]*comp-side',
    r'class="[^"]*metric',
    r'class="[^"]*quote',
    r'class="[^"]*timeline',
    r'class="[^"]*progress',
    r'class="[^"]*cta-',
    r'class="[^"]*animated-counter',
    r'class="[^"]*icon-list',
    r"<svg[\s>]",
    r"<img[\s>]",
    r"<canvas[\s>]",
    r'class="[^"]*code-block',
    r'class="[^"]*styled-table',
    r"<pre[\s>]",
    r"linear-gradient",
    r"radial-gradient",
    r"conic-gradient",
]]

SLIDE_RE = re.compile(
    r'<div\b(?=[^>]*\bclass="slide)(?=[^>]*\bid="s(\d+)")',
    re.IGNORECASE,
)
SLIDE_ALL_RE = re.compile(
    r'<div\b(?=[^>]*\bclass="slide)(?=[^>]*\bid="(s[^"]+)")',
    re.IGNORECASE,
)
SLIDE_BLOCK_RE = re.compile(
    r'(<div\b(?=[^>]*\bclass="slide[^"]*")(?=[^>]*\bid="(s[^"]+)")[^>]*>)(.*?)'
    r'(?=<div\b[^>]*\bclass="slide(?!-)|<div\b[^>]*\bid="nav"|</body>)',
    re.DOTALL | re.IGNORECASE,
)
TOTAL_RE = re.compile(r'<span\s+id="total"[^>]*>\s*(\d+)\s*</span>', re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\{\{IMG:.+?\}\}")
IMG_TAG_RE = re.compile(r"<img\s[^>]*>", re.IGNORECASE)
ALT_RE = re.compile(r'\balt\s*=\s*["\']', re.IGNORECASE)
SPEAKER_NOTES_RE = re.compile(r'class="speaker-notes"', re.IGNORECASE)
DISPLAY_NONE_SLIDE_RE = re.compile(r"\.slide[^{]*\{[^}]*display\s*:\s*none", re.IGNORECASE)
REDUCED_MOTION_RE = re.compile(r"prefers-reduced-motion", re.IGNORECASE)
MATERIAL_URL_RE = re.compile(r"fonts\.googleapis\.com/icon\?family=Material\+Icons\+Round")
MATERIAL_CLASS_RE = re.compile(r'class="material-icons-round"')
HTML_TAG_RE = re.compile(r"<[^>]+>")
NOTES_BLOCK_RE = re.compile(r'<div\s+class="speaker-notes"[^>]*>.*?</div>', re.DOTALL | re.IGNORECASE)
STYLE_TAG_RE = re.compile(r"<style[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE)
SCRIPT_TAG_RE = re.compile(r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
ENTITY_RE = re.compile(r"&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);")
UL_BLOCK_RE = re.compile(r"<ul([^>]*)>(.*?)</ul>", re.DOTALL | re.IGNORECASE)
SYMBOL_CHAR_CLASS = (
    r"[\U0001F300-\U0001FAFF\u2300-\u23FF\u2600-\u27BF"
    r"\u2190-\u21FF\u25A0-\u25FF"
    r"\u2714\u2716\u2717\u2718\u2713\u2715\u2022\u25CF\u25CB"
    r"\u2705\u274C\u274E\u2611\u2612\u2610]"
)
LI_LEADING_SYMBOL_RE = re.compile(
    r"<li[^>]*>\s*"
    r"(?:"
    + SYMBOL_CHAR_CLASS
    + r"|&#x[0-9A-Fa-f]+;"
    r"|<span[^>]*class=\"material-icons-round\"[^>]*>.*?</span>"
    r"|<span[^>]*>\s*(?:" + SYMBOL_CHAR_CLASS + r"|&#x[0-9A-Fa-f]+;)\s*</span>"
    r")",
    re.IGNORECASE,
)
LIST_STYLE_NONE_RE = re.compile(r"list-style\s*:\s*none", re.IGNORECASE)
NO_BULLET_CLASS_RE = re.compile(r'class="[^"]*no-bullet', re.IGNORECASE)
LI_BEFORE_BULLET_RE = re.compile(
    r"li\s*::before\s*\{[^}]*content\s*:\s*['\"]",
    re.IGNORECASE,
)
LI_BEFORE_SUPPRESSED_RE = re.compile(
    r"\.no-bullet\s+li\s*::before\s*\{[^}]*display\s*:\s*none",
    re.IGNORECASE,
)
ANCHOR_RE = re.compile(r"<a\s[^>]*href=['\"]https?://[^'\"]+['\"][^>]*>", re.IGNORECASE)
ANCHOR_TARGET_RE = re.compile(r'\btarget=["\']_blank["\']', re.IGNORECASE)
ANCHOR_REL_RE = re.compile(r'\brel=["\'][^"\']*noopener[^"\']*["\']', re.IGNORECASE)
UL_OL_RE = re.compile(r"<(ul|ol)([^>]*)>", re.IGNORECASE)
TEXT_ALIGN_LEFT_RE = re.compile(r"text-align\s*:\s*left", re.IGNORECASE)
_CSS_RULE_RE = re.compile(r"([^{}]+)\{([^}]*)\}", re.DOTALL)
_CSS_CLASS_IN_SELECTOR_RE = re.compile(r"\.([\w-]+)")
SVG_CONTAINER_RE = re.compile(
    r'(?:max-height\s*:\s*)([\d.]+)(vh|px)',
    re.IGNORECASE,
)
SVG_BLOCK_RE = re.compile(r'<svg\b([^>]*)>(.*?)</svg>', re.DOTALL | re.IGNORECASE)
SVG_VIEWBOX_ATTR_RE = re.compile(r'\bviewBox\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
SVG_RECT_ELEM_RE = re.compile(r'<rect\b([^>]*?)/?>', re.IGNORECASE)
SVG_TEXT_ELEM_RE = re.compile(r'<text\b([^>]*?)>(.*?)</text>', re.DOTALL | re.IGNORECASE)
SVG_CONTENT_Y_RE = re.compile(
    r'<(?:rect|circle|text|line|ellipse)\b[^>]*?\by\s*=\s*["\']?\s*([0-9.]+)',
    re.IGNORECASE,
)
EXTERNAL_LINK_RE = re.compile(r'<a\s[^>]*href="https?://[^"]*"', re.IGNORECASE)
APPENDIX_MARKER_RE = re.compile(r'<!-- Slide \d+: Links \(Appendix\) -->')
APPENDIX_BLOCK_RE = re.compile(
    r'<!-- Slide \d+: Links \(Appendix\) -->.*?(?=<!-- Slide|<div class="counter"|</body>)',
    re.DOTALL | re.IGNORECASE,
)
QR_SIZE_RE = re.compile(r'width\s*:\s*220px', re.IGNORECASE)
BASE64_LINE_RE = re.compile(r'src="data:|;base64,', re.IGNORECASE)
LINE_REF_RE = re.compile(r'\bline (\d+)\b')

NAV_PREV_RE = re.compile(r'<span\b[^>]*id="prev"[^>]*>', re.IGNORECASE)
NAV_NEXT_RE = re.compile(r'<span\b[^>]*id="next"[^>]*>', re.IGNORECASE)
NAV_CURR_RE = re.compile(r'<span\b[^>]*id="curr"[^>]*>', re.IGNORECASE)
NAV_HINT_RE = re.compile(r'<span\b[^>]*id="notes-hint"[^>]*>', re.IGNORECASE)
NAV_NBTN_RE = re.compile(r'<span\b[^>]*class="[^"]*nbtn[^"]*"', re.IGNORECASE)
NAV_BUTTON_IN_NAV_RE = re.compile(r'id="nav".*?<button\b', re.DOTALL | re.IGNORECASE)

NOTES_PANEL_RE = re.compile(r'\bid="notes-panel"', re.IGNORECASE)
NOTES_PANEL_TEXT_RE = re.compile(r'\bid="notes-panel-text"', re.IGNORECASE)
NOTES_PANEL_CLOSE_RE = re.compile(r'\bid="notes-panel-close"', re.IGNORECASE)

CSS_SPEAKER_NOTES_HIDE_RE = re.compile(r'\.speaker-notes\s*\{[^}]*display\s*:\s*none', re.IGNORECASE)
CSS_DECK_PANEL_OPEN_RE = re.compile(r'#deck\.panel-open\s*\{[^}]*height\s*:\s*calc\(100vh\s*-\s*180px\)', re.IGNORECASE)
CSS_BODY_PANEL_NAV_RE = re.compile(r'body\.panel-open\s+#nav\s*\{', re.IGNORECASE)

JS_OPEN_NOTES_WIN_RE = re.compile(r'function\s+openNotesWindow\s*\(')
JS_OPEN_PANEL_RE = re.compile(r'function\s+openNotesPanel\s*\(')
JS_CLOSE_PANEL_RE = re.compile(r'function\s+closeNotesPanel\s*\(')
JS_KEY_N_RE = re.compile(r"""['"]N['"]\s*:.*?openNotesWindow|case\s+['"]N['"]\s*[:\n].*?openNotesWindow""", re.DOTALL)
JS_KEY_B_RE = re.compile(r"""['"]B['"]\s*:.*?[Pp]anel|case\s+['"]B['"]\s*[:\n].*?[Pp]anel""", re.DOTALL)
JS_TOGGLE_NOTES_RE = re.compile(r'\btoggleNotes\s*\(')

MAX_CONTEXT_ISSUES = 10
MAX_REFS_PER_ISSUE = 2


def line_no(html: str, pos: int) -> int:
    """Return the 1-based line number for a character position in html."""
    return html[:pos].count('\n') + 1


def slide_at(pos: int, slide_map: list[tuple[str, int, int]]) -> str:
    """Return the slide ID that contains the given character position."""
    for sid, start, end in slide_map:
        if start <= pos < end:
            return sid
    return "global"


def context_snippet(html_lines: list[str], line_num: int, n: int) -> str:
    """Return ±n lines around line_num (1-based) with base64 content redacted."""
    start = max(0, line_num - n - 1)
    end = min(len(html_lines), line_num + n)
    out = []
    for i in range(start, end):
        ln = i + 1
        raw = html_lines[i]
        if BASE64_LINE_RE.search(raw):
            kb = max(1, len(raw.encode()) // 1024)
            display = f'[base64 data omitted — {kb}kb]'
        else:
            display = raw.rstrip()[:120]
        marker = '→' if ln == line_num else ' '
        out.append(f"      {marker}{ln:5d}: {display}")
    return '\n'.join(out)


def strip_html(text: str) -> str:
    text = NOTES_BLOCK_RE.sub("", text)
    text = STYLE_TAG_RE.sub("", text)
    text = SCRIPT_TAG_RE.sub("", text)
    text = HTML_TAG_RE.sub(" ", text)
    text = ENTITY_RE.sub(" ", text)
    return text


def count_visible_words(html_block: str) -> int:
    return len(strip_html(html_block).split())


def has_visual(html_block: str) -> bool:
    return any(pat.search(html_block) for pat in VISUAL_PATTERNS)


def _svg_float(attrs: str, name: str, default: float = 0.0) -> float:
    escaped = re.escape(name)
    m = re.search(r'\b' + escaped + r'\s*=\s*["\']?\s*([-0-9.]+)', attrs, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(escaped + r'\s*:\s*([-0-9.]+)', attrs, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return default


def _svg_text_longest_line(inner: str) -> str:
    chunks = re.split(r'<[^>]+>', inner)
    chunks = [c.strip() for c in chunks if c.strip()]
    return max(chunks, key=len) if chunks else ''


def validate(html_path: Path) -> tuple[list[str], list[str], list[str]]:
    passes: list[str] = []
    warns: list[str] = []
    fails: list[str] = []

    if not html_path.is_file():
        raise FileNotFoundError(f"'{html_path}' not found or is not a file.")

    if html_path.stat().st_size > MAX_FILE_SIZE:
        warns.append("File exceeds 20 MB — regex performance may degrade")

    html = html_path.read_text(encoding="utf-8")

    # 1. Slide IDs — sequential id="s1", s2, ... with no gaps or dupes
    all_slide_ids = [m.group(1) for m in SLIDE_ALL_RE.finditer(html)]
    numeric_ids = [int(m.group(1)) for m in SLIDE_RE.finditer(html)]
    if not all_slide_ids:
        fails.append("No slides found (expected <div class=\"slide\" id=\"sN\">)")
        return passes, warns, fails

    if not numeric_ids and all_slide_ids:
        warns.append("Slide IDs: no numeric slide IDs found (e.g. s1, s2) — sequential check skipped")
    else:
        expected = list(range(1, len(numeric_ids) + 1))
        if numeric_ids == expected:
            passes.append(f"Slide IDs: sequential s1–s{len(numeric_ids)}")
        else:
            fails.append(f"Slide IDs not sequential: got {numeric_ids}, expected {expected}")

    if len(numeric_ids) != len(set(numeric_ids)):
        dupes = sorted(k for k, v in Counter(numeric_ids).items() if v > 1)
        fails.append(f"Duplicate slide IDs: {dupes}")

    # 2. Total counter — <span id="total"> matches actual slide count
    total_slide_count = len(numeric_ids)
    total_match = TOTAL_RE.search(html)
    if total_match:
        declared = int(total_match.group(1))
        if declared == total_slide_count:
            passes.append(f"Total counter: {declared} matches actual slide count")
        else:
            fails.append(f"Total counter says {declared} but there are {total_slide_count} slides")
    else:
        warns.append("No <span id=\"total\"> found — slide counter may be missing")

    # 3. Orphan placeholders — leftover {{IMG:...}} tokens not yet embedded
    placeholder_matches = list(PLACEHOLDER_RE.finditer(html))
    if placeholder_matches:
        details = [
            f"{m.group()} at line {line_no(html, m.start())}"
            for m in placeholder_matches[:3]
        ]
        fails.append(
            f"Orphan placeholders ({len(placeholder_matches)}): {', '.join(details)}"
            f"{'...' if len(placeholder_matches) > 3 else ''}"
        )
    else:
        passes.append("No orphan {{IMG:...}} placeholders")

    # 4. Visual component — every slide has at least one visual element
    # 5. Word count — flags slides exceeding 30 visible words
    slide_blocks = list(SLIDE_BLOCK_RE.finditer(html))
    slide_map = [(m.group(2), m.start(), m.end()) for m in slide_blocks]

    if not slide_blocks and all_slide_ids:
        warns.append("Could not extract slide blocks for per-slide checks (unusual HTML structure)")

    no_visual: list[str] = []
    over_30: list[tuple[str, int]] = []
    if slide_blocks:
        for m in slide_blocks:
            sid = m.group(2)
            block = m.group(3)
            if not has_visual(block):
                no_visual.append(sid)
            wc = count_visible_words(block)
            if wc > MAX_WORDS_PER_SLIDE:
                over_30.append((sid, wc))

        if no_visual:
            fails.append(f"Slides without visual component: {no_visual}")
        else:
            passes.append("All slides have a visual component")

        if over_30:
            details = ", ".join(f"{s}={w}w" for s, w in over_30)
            warns.append(f"Slides over {MAX_WORDS_PER_SLIDE} words: {details}")
        else:
            passes.append(f"All slides within {MAX_WORDS_PER_SLIDE}-word limit")

    # 6. Speaker notes — if any slide has notes, all should (consistency)
    notes_count = len(SPEAKER_NOTES_RE.findall(html))
    if notes_count == 0:
        passes.append("No speaker notes (consistent)")
    elif notes_count == total_slide_count:
        passes.append(f"Speaker notes on all {notes_count} slides")
    else:
        warns.append(f"Speaker notes on {notes_count}/{total_slide_count} slides (inconsistent)")

    # 7. Accessibility — <img> tags missing alt attribute
    img_matches = list(IMG_TAG_RE.finditer(html))
    missing_alt = [(m.group(), m.start()) for m in img_matches if not ALT_RE.search(m.group())]
    if img_matches and not missing_alt:
        passes.append(f"All {len(img_matches)} <img> tags have alt attributes")
    elif missing_alt:
        details = [
            f"{slide_at(pos, slide_map)} line {line_no(html, pos)}"
            for _, pos in missing_alt[:3]
        ]
        warns.append(
            f"{len(missing_alt)} <img> tag(s) missing alt attribute: {', '.join(details)}"
            f"{'...' if len(missing_alt) > 3 else ''}"
        )
    else:
        passes.append("No <img> tags (nothing to check)")

    html_no_style = STYLE_TAG_RE.sub("", SCRIPT_TAG_RE.sub("", html))

    # 8. Slide transitions — warns if display:none is used instead of opacity
    if DISPLAY_NONE_SLIDE_RE.search(html_no_style):
        fails.append("Slide transitions use display:none — should use opacity crossfade")
    else:
        passes.append("Slide transitions use opacity (no display:none)")

    # 9. Reduced motion — checks for prefers-reduced-motion media query
    if REDUCED_MOTION_RE.search(html):
        passes.append("prefers-reduced-motion respected")
    else:
        warns.append("No prefers-reduced-motion media query found")

    # 10. Material Icons — verifies the correct stylesheet URL and class name
    has_icons = MATERIAL_CLASS_RE.search(html)
    if has_icons:
        if MATERIAL_URL_RE.search(html):
            passes.append("Material Icons: correct URL and class")
        else:
            fails.append("Material Icons class used but stylesheet URL is wrong or missing")
    else:
        passes.append("No Material Icons used (nothing to check)")

    # 11. Double bullets — warns when <li> uses leading symbols/emojis but <ul> missing list-style:none
    double_bullet_lists: list[str] = []
    for m in slide_blocks:
        sid = m.group(2)
        slide_block = m.group(3)
        block_start = m.start() + len(m.group(1))
        has_before_bullets = LI_BEFORE_BULLET_RE.search(slide_block)
        has_before_suppression = LI_BEFORE_SUPPRESSED_RE.search(slide_block)
        for ul_match in UL_BLOCK_RE.finditer(slide_block):
            ul_attrs = ul_match.group(1)
            ul_body = ul_match.group(2)
            if LI_LEADING_SYMBOL_RE.search(ul_body):
                has_inline_fix = LIST_STYLE_NONE_RE.search(ul_attrs)
                has_class_fix = NO_BULLET_CLASS_RE.search(ul_attrs)
                ln = line_no(html, block_start + ul_match.start())
                if not has_inline_fix and not has_class_fix:
                    snippet = ul_body.strip()[:60].replace("\n", " ")
                    double_bullet_lists.append(f"{sid} line {ln}: {snippet}")
                elif has_before_bullets and not has_class_fix and not has_before_suppression:
                    snippet = ul_body.strip()[:60].replace("\n", " ")
                    double_bullet_lists.append(f"{sid} line {ln} (::before pseudo-bullet): {snippet}")
    if double_bullet_lists:
        warns.append(
            f"{len(double_bullet_lists)} <ul> with symbol/emoji <li> missing "
            f"list-style:none — first: {double_bullet_lists[0]}"
        )
    else:
        passes.append("No double-bullet lists (symbols + default bullets)")

    # 12. QR appendix — warn if external links exist but no appendix slide
    external_links = EXTERNAL_LINK_RE.findall(html)
    has_appendix = bool(APPENDIX_MARKER_RE.search(html))
    if external_links and not has_appendix:
        warns.append(
            f"Deck has {len(external_links)} external link(s) but no QR appendix slide — "
            f"run generate_qr_appendix.py"
        )
    elif external_links and has_appendix:
        passes.append("QR appendix slide present for external links")
        appendix_blocks = APPENDIX_BLOCK_RE.findall(html)
        for i, block in enumerate(appendix_blocks, 1):
            qr_count = len(QR_SIZE_RE.findall(block))
            if qr_count > MAX_QR_PER_SLIDE:
                warns.append(
                    f"QR appendix slide {i} has {qr_count} QR codes (max {MAX_QR_PER_SLIDE}) — "
                    f"re-run generate_qr_appendix.py to split into multiple slides"
                )

    # 13. Link attributes — <a> tags must have target="_blank" and rel="noopener"
    anchor_matches = list(ANCHOR_RE.finditer(html))
    bad_anchors: list[str] = []
    for am in anchor_matches:
        tag = am.group()
        if not ANCHOR_TARGET_RE.search(tag) or not ANCHOR_REL_RE.search(tag):
            sid = slide_at(am.start(), slide_map)
            ln = line_no(html, am.start())
            bad_anchors.append(f"{sid} line {ln}: {tag[:60]}")
    if bad_anchors:
        warns.append(
            f"{len(bad_anchors)} <a> tag(s) missing target=\"_blank\" or rel=\"noopener\": "
            f"{bad_anchors[0]}{'  (+{} more)'.format(len(bad_anchors) - 1) if len(bad_anchors) > 1 else ''}"
        )
    elif anchor_matches:
        passes.append(f"All {len(anchor_matches)} <a> tag(s) have target=_blank and rel=noopener")

    # 14. List alignment — <ul>/<ol> with bullets should have text-align:left
    # Build a set of CSS class names (and sentinel tags) that provide text-align:left
    # by scanning the <style> block, so class-based alignment isn't a false positive.
    _css_left_classes: set[str] = set()
    _css_left_tags: set[str] = set()
    style_matches = STYLE_TAG_RE.findall(html)
    for style_block in style_matches:
        css_content = re.sub(r'<style[^>]*>', '', style_block)
        css_content = css_content.replace('</style>', '')
        for rule_m in _CSS_RULE_RE.finditer(css_content):
            if TEXT_ALIGN_LEFT_RE.search(rule_m.group(2)):
                sel = rule_m.group(1).lower()
                for cls in _CSS_CLASS_IN_SELECTOR_RE.findall(sel):
                    _css_left_classes.add(cls.strip())
                if "ul" in sel:
                    _css_left_tags.add("ul")
                if "ol" in sel:
                    _css_left_tags.add("ol")

    list_missing_align: list[str] = []
    for sb in slide_blocks:
        sid = sb.group(2)
        for ul_match in UL_OL_RE.finditer(sb.group(0)):
            tag = ul_match.group(1).lower()
            attrs = ul_match.group(2)
            if TEXT_ALIGN_LEFT_RE.search(attrs):
                continue
            if tag in _css_left_tags:
                continue
            cls_m = re.search(r'\bclass=["\']([^"\']*)["\']', attrs, re.IGNORECASE)
            if cls_m and any(c in _css_left_classes for c in cls_m.group(1).split()):
                continue
            ln = line_no(html, sb.start() + ul_match.start())
            list_missing_align.append(f"{sid} line {ln}")
    if list_missing_align:
        warns.append(
            f"{len(list_missing_align)} <ul>/<ol> element(s) without explicit text-align:left: "
            f"{', '.join(list_missing_align[:3])}{'...' if len(list_missing_align) > 3 else ''}"
        )
    else:
        passes.append("All <ul>/<ol> elements have text-align:left")

    # 15. SVG max-height — SVG containers should have max-height >= 58vh
    # Search within slide blocks to get slide ID and line number without
    # position-mapping issues from html_no_style.
    svg_low_height: list[str] = []
    for m in slide_blocks:
        sid = m.group(2)
        block_start = m.start() + len(m.group(1))
        for svg_m in SVG_CONTAINER_RE.finditer(m.group(3)):
            val = float(svg_m.group(1))
            unit = svg_m.group(2).lower()
            if unit == "vh" and val < MIN_SVG_VH:
                ln = line_no(html, block_start + svg_m.start())
                svg_low_height.append(f"{sid} line {ln}: {val}vh")
    if svg_low_height:
        warns.append(
            f"SVG container(s) with max-height below {MIN_SVG_VH}vh: "
            f"{', '.join(svg_low_height)} — increase to at least {MIN_SVG_VH}vh"
        )
    else:
        passes.append(f"SVG container max-height is >= {MIN_SVG_VH}vh (or not set via inline style)")

    # 16. Nav HTML structure
    nav_fails = []
    if not NAV_PREV_RE.search(html):
        nav_fails.append('<span id="prev"> missing')
    if not NAV_NEXT_RE.search(html):
        nav_fails.append('<span id="next"> missing')
    if not NAV_CURR_RE.search(html):
        nav_fails.append('<span id="curr"> missing')
    if not NAV_HINT_RE.search(html):
        nav_fails.append('<span id="notes-hint"> missing')
    if not NAV_NBTN_RE.search(html):
        nav_fails.append('no <span class="nbtn"> elements found (spec requires spans, not buttons)')
    if nav_fails:
        fails.append(f"Nav HTML structure: {'; '.join(nav_fails)}")
    else:
        passes.append("Nav HTML structure: prev/next/curr/notes-hint/nbtn all present")
    if NAV_BUTTON_IN_NAV_RE.search(html):
        warns.append('Nav contains <button> elements — spec requires <span class="nbtn"> instead')

    # 17. Notes panel HTML (only when speaker notes present)
    if notes_count > 0:
        panel_fails = []
        if not NOTES_PANEL_RE.search(html):
            panel_fails.append('id="notes-panel" missing')
        if not NOTES_PANEL_TEXT_RE.search(html):
            panel_fails.append('id="notes-panel-text" missing')
        if not NOTES_PANEL_CLOSE_RE.search(html):
            panel_fails.append('id="notes-panel-close" missing')
        if panel_fails:
            fails.append(f"Notes panel HTML: {'; '.join(panel_fails)}")
        else:
            passes.append("Notes panel HTML: notes-panel/notes-panel-text/notes-panel-close all present")

    # 18. Notes CSS (only when speaker notes present)
    if notes_count > 0:
        style_text = " ".join(STYLE_TAG_RE.findall(html))
        css_warns = []
        if not CSS_SPEAKER_NOTES_HIDE_RE.search(style_text):
            css_warns.append(".speaker-notes { display: none } rule missing")
        if not CSS_DECK_PANEL_OPEN_RE.search(style_text):
            css_warns.append("#deck.panel-open { height: calc(100vh - 180px) } rule missing")
        if not CSS_BODY_PANEL_NAV_RE.search(style_text):
            css_warns.append("body.panel-open #nav rule missing")
        if css_warns:
            for w in css_warns:
                warns.append(f"Notes CSS: {w}")
        else:
            passes.append("Notes CSS: speaker-notes/deck.panel-open/body.panel-open rules all present")

    # 19. JS wiring (only when speaker notes present)
    if notes_count > 0:
        script_text = " ".join(SCRIPT_TAG_RE.findall(html))
        if JS_TOGGLE_NOTES_RE.search(script_text):
            fails.append(
                "JS wiring: toggleNotes() found — old pattern; "
                "replace with openNotesWindow / openNotesPanel / closeNotesPanel"
            )
        else:
            js_warns = []
            if not JS_OPEN_NOTES_WIN_RE.search(script_text):
                js_warns.append("openNotesWindow() not defined")
            if not JS_OPEN_PANEL_RE.search(script_text):
                js_warns.append("openNotesPanel() not defined")
            if not JS_CLOSE_PANEL_RE.search(script_text):
                js_warns.append("closeNotesPanel() not defined")
            if not JS_KEY_N_RE.search(script_text):
                js_warns.append("'N' key binding for openNotesWindow not found")
            if not JS_KEY_B_RE.search(script_text):
                js_warns.append("'B' key binding for panel toggle not found")
            if js_warns:
                warns.append(f"JS wiring: {'; '.join(js_warns)}")
            else:
                passes.append(
                    "JS wiring: openNotesWindow/openNotesPanel/closeNotesPanel and N/B bindings all present"
                )

    # 20. SVG text overflow — estimate text width vs containing rect width
    # 21. SVG viewBox top-gap — first content element far below viewBox top
    svg_overflows: list[str] = []
    svg_topgaps: list[str] = []
    for sb in slide_blocks:
        sid = sb.group(2)
        for svg_m in SVG_BLOCK_RE.finditer(sb.group(3)):
            svg_attrs = svg_m.group(1)
            svg_body  = svg_m.group(2)
            svg_pos   = sb.start() + len(sb.group(1)) + svg_m.start()

            rects = []
            for r in SVG_RECT_ELEM_RE.finditer(svg_body):
                a  = r.group(1)
                rx = _svg_float(a, 'x')
                ry = _svg_float(a, 'y')
                rw = _svg_float(a, 'width')
                rh = _svg_float(a, 'height')
                if rw > 0 and rh > 0:
                    rects.append((rx, ry, rw, rh))

            for t in SVG_TEXT_ELEM_RE.finditer(svg_body):
                t_attrs = t.group(1)
                t_inner = t.group(2)
                tx      = _svg_float(t_attrs, 'x')
                ty      = _svg_float(t_attrs, 'y')
                fs      = _svg_float(t_attrs, 'font-size', 12.0)
                text    = _svg_text_longest_line(t_inner)
                if not text or fs <= 0:
                    continue
                est_w = len(text) * fs * SVG_CHAR_WIDTH
                containing = [
                    (cw * ch, cx, cy, cw, ch)
                    for (cx, cy, cw, ch) in rects
                    if cx - 5 <= tx <= cx + cw + 5 and cy - 5 <= ty <= cy + ch + 5
                ]
                if not containing:
                    continue
                _, cx, cy, cw, ch = min(containing, key=lambda c: c[0])
                if est_w > cw + SVG_OVERFLOW_TOLERANCE:
                    ln = line_no(html, svg_pos + t.start())
                    svg_overflows.append(
                        f"{sid} line {ln}: \"{text[:40]}\" ~{est_w:.0f}px in {cw:.0f}px rect"
                    )

            vb_m = SVG_VIEWBOX_ATTR_RE.search(svg_attrs)
            if vb_m:
                parts = vb_m.group(1).split()
                if len(parts) == 4:
                    try:
                        vb_y = float(parts[1])
                        vb_h = float(parts[3])
                        ys   = [float(m.group(1)) for m in SVG_CONTENT_Y_RE.finditer(svg_body)]
                        if ys and vb_h > 0:
                            min_y = min(ys)
                            gap   = (min_y - vb_y) / vb_h
                            if gap > SVG_GAP_THRESHOLD:
                                ln = line_no(html, svg_pos)
                                svg_topgaps.append(
                                    f"{sid} line {ln}: first y={min_y:.0f} in viewBox "
                                    f"height={vb_h:.0f} ({gap*100:.0f}% top gap)"
                                )
                    except (ValueError, IndexError):
                        pass

    if svg_overflows:
        warns.append(
            f"{len(svg_overflows)} SVG text element(s) may overflow containing rect — "
            f"run svg_calc.py textbox to confirm: {svg_overflows[0]}"
            + (f"  (+{len(svg_overflows) - 1} more)" if len(svg_overflows) > 1 else "")
        )
    else:
        passes.append("No SVG text overflow detected (estimated widths within rect bounds)")

    if svg_topgaps:
        warns.append(
            f"{len(svg_topgaps)} SVG viewBox(es) with top gap > {SVG_GAP_THRESHOLD*100:.0f}%: "
            f"{svg_topgaps[0]}"
            + (f"  (+{len(svg_topgaps) - 1} more)" if len(svg_topgaps) > 1 else "")
        )
    else:
        passes.append(f"SVG viewBox top gaps within {SVG_GAP_THRESHOLD*100:.0f}% threshold")

    # 22. SVG rect overflow — inner <rect> escaping its containing <rect>
    SVG_RECT_OVERFLOW_TOLERANCE = 5.0
    rect_overflows: list[str] = []
    for sb in slide_blocks:
        sid = sb.group(2)
        for svg_m in SVG_BLOCK_RE.finditer(sb.group(3)):
            svg_body = svg_m.group(2)
            svg_pos  = sb.start() + len(sb.group(1)) + svg_m.start()

            rects = []
            for r in SVG_RECT_ELEM_RE.finditer(svg_body):
                a  = r.group(1)
                rx = _svg_float(a, 'x')
                ry = _svg_float(a, 'y')
                rw = _svg_float(a, 'width')
                rh = _svg_float(a, 'height')
                if rw > 0 and rh > 0:
                    rects.append((rx, ry, rw, rh, r.start()))

            for (rx, ry, rw, rh, r_pos) in rects:
                containers = [
                    (cw * ch, cx, cy, cw, ch)
                    for (cx, cy, cw, ch, _) in rects
                    if cx - 5 <= rx and cy - 5 <= ry
                    and rx <= cx + cw + 5 and ry <= cy + ch + 5
                    and (cw > rw or ch > rh)
                    and not (cx == rx and cy == ry and cw == rw and ch == rh)
                ]
                if not containers:
                    continue
                _, cx, cy, cw, ch = min(containers, key=lambda c: c[0])
                bottom_over = (ry + rh) - (cy + ch)
                right_over  = (rx + rw) - (cx + cw)
                if bottom_over > SVG_RECT_OVERFLOW_TOLERANCE or right_over > SVG_RECT_OVERFLOW_TOLERANCE:
                    ln = line_no(html, svg_pos + r_pos)
                    parts = []
                    if bottom_over > SVG_RECT_OVERFLOW_TOLERANCE:
                        parts.append(f"bottom overflow +{bottom_over:.0f}px")
                    if right_over > SVG_RECT_OVERFLOW_TOLERANCE:
                        parts.append(f"right overflow +{right_over:.0f}px")
                    rect_overflows.append(
                        f"{sid} line {ln}: inner rect y={ry:.0f}+{rh:.0f} in container "
                        f"y={cy:.0f}+{ch:.0f} — {', '.join(parts)}"
                    )

    if rect_overflows:
        warns.append(
            f"{len(rect_overflows)} SVG inner rect(s) overflow their container — "
            f"run svg_calc.py stack --container-y to fix: {rect_overflows[0]}"
            + (f"  (+{len(rect_overflows) - 1} more)" if len(rect_overflows) > 1 else "")
        )
    else:
        passes.append("No SVG rect containment overflow detected")

    return passes, warns, fails


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a slide deck HTML file against the HTML Presentation skill rules."
    )
    parser.add_argument("html_file", help="Path to the HTML deck file")
    parser.add_argument(
        "--context", "-c", type=int, default=0, metavar="N",
        help="Show ±N lines of context around each warning/failure (base64 redacted). "
             "Recommended: --context 5. Capped at 10 issues × 2 refs each.",
    )
    args = parser.parse_args()

    html_path = Path(args.html_file)
    if not html_path.is_file():
        print(f"Error: '{html_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        passes, warns, fails = validate(html_path)
    except (UnicodeDecodeError, OSError) as e:
        print(f"Error reading '{html_path}': {e}", file=sys.stderr)
        sys.exit(1)

    html_lines: list[str] = []
    if args.context > 0:
        html_lines = html_path.read_text(encoding="utf-8").splitlines()

    def print_with_context(messages: list[str], symbol: str, issues_shown: list[int]) -> None:
        """Print each message and, if context requested and budget allows, its code snippet."""
        for msg in messages:
            print(f"    {symbol} {msg}")
            if args.context > 0 and issues_shown[0] < MAX_CONTEXT_ISSUES:
                refs = LINE_REF_RE.findall(msg)[:MAX_REFS_PER_ISSUE]
                for ref in refs:
                    print(context_snippet(html_lines, int(ref), args.context))
                    issues_shown[0] += 1
                    if issues_shown[0] >= MAX_CONTEXT_ISSUES:
                        remaining = sum(len(LINE_REF_RE.findall(m)) for m in messages)
                        print(f"\n      ... context limit reached ({MAX_CONTEXT_ISSUES} issues) — "
                              f"re-run without --context to see all messages")
                        return

    issues_shown = [0]

    if passes:
        print(f"\n  ✓ PASS ({len(passes)})")
        for p in passes:
            print(f"    ✓ {p}")

    if warns:
        print(f"\n  ⚠ WARN ({len(warns)})")
        print_with_context(warns, '⚠', issues_shown)

    if fails:
        print(f"\n  ✗ FAIL ({len(fails)})")
        print_with_context(fails, '✗', issues_shown)

    total = len(passes) + len(warns) + len(fails)
    print(f"\n  {len(passes)}/{total} passed, {len(warns)} warnings, {len(fails)} failures")

    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
