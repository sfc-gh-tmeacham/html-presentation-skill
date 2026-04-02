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
    r'(?=<div\b(?=[^>]*\bclass="slide[\s"])(?=[^>]*\bid="s)|<div\s+class="nav"|</body>)',
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
ENTITY_RE = re.compile(r"&\w+;")
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
_CSS_CLASS_IN_SELECTOR_RE = re.compile(r"\.([ \w-]+)")
SVG_CONTAINER_RE = re.compile(
    r'(?:max-height\s*:\s*)([\d.]+)(vh|px)',
    re.IGNORECASE,
)
EXTERNAL_LINK_RE = re.compile(r'<a\s[^>]*href="https?://[^"]*"', re.IGNORECASE)
APPENDIX_MARKER_RE = re.compile(r'<!-- Slide \d+: Links \(Appendix\) -->')


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


def validate(html_path: Path) -> tuple[list[str], list[str], list[str]]:
    html = html_path.read_text(encoding="utf-8")
    passes: list[str] = []
    warns: list[str] = []
    fails: list[str] = []

    all_slide_ids = [m.group(1) for m in SLIDE_ALL_RE.finditer(html)]
    numeric_ids = [int(m.group(1)) for m in SLIDE_RE.finditer(html)]
    if not all_slide_ids:
        fails.append("No slides found (expected <div class=\"slide\" id=\"sN\">)")
        return passes, warns, fails

    expected = list(range(1, len(numeric_ids) + 1))
    if numeric_ids == expected:
        passes.append(f"Slide IDs: sequential s1–s{len(numeric_ids)}")
    else:
        fails.append(f"Slide IDs not sequential: got {numeric_ids}, expected {expected}")

    if len(numeric_ids) != len(set(numeric_ids)):
        dupes = sorted(k for k, v in Counter(numeric_ids).items() if v > 1)
        fails.append(f"Duplicate slide IDs: {dupes}")

    total_slide_count = len(all_slide_ids)
    total_match = TOTAL_RE.search(html)
    if total_match:
        declared = int(total_match.group(1))
        if declared == total_slide_count:
            passes.append(f"Total counter: {declared} matches actual slide count")
        else:
            fails.append(f"Total counter says {declared} but there are {total_slide_count} slides")
    else:
        warns.append("No <span id=\"total\"> found — slide counter may be missing")

    placeholders = PLACEHOLDER_RE.findall(html)
    if placeholders:
        fails.append(f"Orphan placeholders ({len(placeholders)}): {placeholders[:3]}{'...' if len(placeholders) > 3 else ''}")
    else:
        passes.append("No orphan {{IMG:...}} placeholders")

    slide_blocks = list(SLIDE_BLOCK_RE.finditer(html))
    no_visual: list[str] = []
    over_30: list[tuple[str, int]] = []
    for m in slide_blocks:
        sid = m.group(2)
        block = m.group(3)
        if not has_visual(block):
            no_visual.append(sid)
        wc = count_visible_words(block)
        if wc > 30:
            over_30.append((sid, wc))

    if no_visual:
        fails.append(f"Slides without visual component: {no_visual}")
    else:
        passes.append("All slides have a visual component")

    if over_30:
        details = ", ".join(f"{s}={w}w" for s, w in over_30)
        warns.append(f"Slides over 30 words: {details}")
    else:
        passes.append("All slides within 30-word limit")

    notes_count = len(SPEAKER_NOTES_RE.findall(html))
    if notes_count == 0:
        passes.append("No speaker notes (consistent)")
    elif notes_count == total_slide_count:
        passes.append(f"Speaker notes on all {notes_count} slides")
    else:
        warns.append(f"Speaker notes on {notes_count}/{total_slide_count} slides (inconsistent)")

    img_tags = IMG_TAG_RE.findall(html)
    missing_alt = [t[:60] for t in img_tags if not ALT_RE.search(t)]
    if img_tags and not missing_alt:
        passes.append(f"All {len(img_tags)} <img> tags have alt attributes")
    elif missing_alt:
        warns.append(f"{len(missing_alt)} <img> tag(s) missing alt attribute")
    else:
        passes.append("No <img> tags (nothing to check)")

    if DISPLAY_NONE_SLIDE_RE.search(html):
        fails.append("Slide transitions use display:none — should use opacity crossfade")
    else:
        passes.append("Slide transitions use opacity (no display:none)")

    if REDUCED_MOTION_RE.search(html):
        passes.append("prefers-reduced-motion respected")
    else:
        warns.append("No prefers-reduced-motion media query found")

    has_icons = MATERIAL_CLASS_RE.search(html)
    if has_icons:
        if MATERIAL_URL_RE.search(html):
            passes.append("Material Icons: correct URL and class")
        else:
            fails.append("Material Icons class used but stylesheet URL is wrong or missing")
    else:
        passes.append("No Material Icons used (nothing to check)")

    has_before_bullets = LI_BEFORE_BULLET_RE.search(html)
    has_before_suppression = LI_BEFORE_SUPPRESSED_RE.search(html)

    double_bullet_lists: list[str] = []
    for ul_match in UL_BLOCK_RE.finditer(html):
        ul_attrs = ul_match.group(1)
        ul_body = ul_match.group(2)
        if LI_LEADING_SYMBOL_RE.search(ul_body):
            has_inline_fix = LIST_STYLE_NONE_RE.search(ul_attrs)
            has_class_fix = NO_BULLET_CLASS_RE.search(ul_attrs)
            if not has_inline_fix and not has_class_fix:
                snippet = ul_body.strip()[:80].replace("\n", " ")
                double_bullet_lists.append(snippet)
            elif has_before_bullets and not has_class_fix and not has_before_suppression:
                snippet = ul_body.strip()[:80].replace("\n", " ")
                double_bullet_lists.append(f"(::before pseudo-bullet) {snippet}")
    if double_bullet_lists:
        warns.append(
            f"{len(double_bullet_lists)} <ul> with symbol/emoji <li> missing "
            f"list-style:none — first: {double_bullet_lists[0]}..."
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
        appendix_blocks = re.findall(
            r'<!-- Slide \d+: Links \(Appendix\) -->.*?(?=<!-- Slide|<div class="counter"|</body>)',
            html, re.DOTALL | re.IGNORECASE,
        )
        for i, block in enumerate(appendix_blocks, 1):
            qr_count = len(re.findall(r'width:220px;height:220px', block))
            if qr_count > 6:
                warns.append(
                    f"QR appendix slide {i} has {qr_count} QR codes (max 6) — "
                    f"re-run generate_qr_appendix.py to split into multiple slides"
                )

    # 13. Rule 13 — <a> tags must have target="_blank" and rel="noopener"
    anchor_tags = ANCHOR_RE.findall(html)
    bad_anchors: list[str] = []
    for tag in anchor_tags:
        if not ANCHOR_TARGET_RE.search(tag) or not ANCHOR_REL_RE.search(tag):
            bad_anchors.append(tag[:80])
    if bad_anchors:
        warns.append(
            f"{len(bad_anchors)} <a> tag(s) missing target=\"_blank\" or rel=\"noopener\""
        )
    elif anchor_tags:
        passes.append(f"All {len(anchor_tags)} <a> tag(s) have target=_blank and rel=noopener")

    # 14. Rule 12 — <ul>/<ol> with bullets should have text-align:left
    # Build a set of CSS class names (and sentinel tags) that provide text-align:left
    # by scanning the <style> block, so class-based alignment isn't a false positive.
    _css_left_classes: set[str] = set()
    _css_left_tags: set[str] = set()
    style_m = STYLE_TAG_RE.search(html)
    if style_m:
        for rule_m in _CSS_RULE_RE.finditer(style_m.group(0)):
            if TEXT_ALIGN_LEFT_RE.search(rule_m.group(2)):
                sel = rule_m.group(1).lower()
                for cls in _CSS_CLASS_IN_SELECTOR_RE.findall(sel):
                    _css_left_classes.add(cls.strip())
                if "ul" in sel:
                    _css_left_tags.add("ul")
                if "ol" in sel:
                    _css_left_tags.add("ol")

    list_missing_align: int = 0
    for ul_match in UL_OL_RE.finditer(html):
        tag = ul_match.group(1).lower()
        attrs = ul_match.group(2)
        if TEXT_ALIGN_LEFT_RE.search(attrs):
            continue
        if tag in _css_left_tags:
            continue
        cls_m = re.search(r'\bclass=["\']([^"\']*)["\']', attrs, re.IGNORECASE)
        if cls_m and any(c in _css_left_classes for c in cls_m.group(1).split()):
            continue
        list_missing_align += 1
    if list_missing_align:
        warns.append(
            f"{list_missing_align} <ul>/<ol> element(s) without explicit text-align:left"
        )
    else:
        passes.append("All <ul>/<ol> elements have text-align:left")

    # 15. Rule 16 — SVG containers should have max-height >= 58vh
    # Strip <style>/<script> blocks first to avoid false positives from CSS rules.
    html_no_style = STYLE_TAG_RE.sub("", SCRIPT_TAG_RE.sub("", html))
    svg_low_height: list[str] = []
    for m in SVG_CONTAINER_RE.finditer(html_no_style):
        val = float(m.group(1))
        unit = m.group(2).lower()
        if unit == "vh" and val < 58:
            svg_low_height.append(f"{val}vh")
    if svg_low_height:
        warns.append(
            f"SVG container(s) with max-height below 58vh: {svg_low_height} — "
            f"increase to at least 58vh to avoid empty slide bands"
        )
    else:
        passes.append("SVG container max-height is >= 58vh (or not set via inline style)")

    return passes, warns, fails


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a slide deck HTML file against the HTML Presentation skill rules."
    )
    parser.add_argument("html_file", help="Path to the HTML deck file")
    args = parser.parse_args()

    html_path = Path(args.html_file)
    if not html_path.is_file():
        print(f"Error: '{html_path}' not found.", file=sys.stderr)
        sys.exit(1)

    passes, warns, fails = validate(html_path)

    if passes:
        print(f"\n  ✓ PASS ({len(passes)})")
        for p in passes:
            print(f"    ✓ {p}")

    if warns:
        print(f"\n  ⚠ WARN ({len(warns)})")
        for w in warns:
            print(f"    ⚠ {w}")

    if fails:
        print(f"\n  ✗ FAIL ({len(fails)})")
        for f in fails:
            print(f"    ✗ {f}")

    total = len(passes) + len(warns) + len(fails)
    print(f"\n  {len(passes)}/{total} passed, {len(warns)} warnings, {len(fails)} failures")

    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
