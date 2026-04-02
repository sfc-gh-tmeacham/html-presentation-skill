#!/usr/bin/env python3
"""Append QR-code appendix slide(s) to an HTML presentation.

Scans the deck for all ``<a href="https://...">`` links, generates an inline
SVG QR code for each unique URL using the **segno** library, and inserts
appendix slides just before the slide counter.  A maximum of 6 QR codes are
placed on each slide; if there are more than 6 links, additional slides are
generated automatically (e.g. "Resources (1/2)", "Resources (2/2)").  The
slide counter's total is updated automatically.

The generated SVG QR codes are fully self-contained — no external images,
no JavaScript, no runtime dependencies.

Usage::

    python run_script.py generate_qr_appendix.py <deck.html>
"""

import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

try:
    import segno
except ImportError:
    print(
        "Error: 'segno' is not installed.  "
        "Run this script via run_script.py to auto-install dependencies.",
        file=sys.stderr,
    )
    sys.exit(1)

LINK_RE = re.compile(
    r'<a\s[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r'<[^>]+>')
PAGE_TITLE_RE = re.compile(r'<title[^>]*>([^<]+)</title>', re.IGNORECASE)
ACCENT_RE = re.compile(r"--accent:\s*(#[0-9A-Fa-f]{3,8})\s*;")
TOTAL_RE = re.compile(r'(<span\s+id="total">)\d+(</span>)')
COUNTER_RE = re.compile(r'<div\s+class="counter"')
SLIDE_ID_RE = re.compile(r'<div\s+class="slide[^"]*"[^>]*id="s(\d+)"', re.IGNORECASE)


def extract_links(html: str) -> list[tuple[str, str]]:
    """Return deduplicated (url, title) pairs in document order.

    Title resolution priority:
    1. Anchor text from the first ``<a>`` for each URL (if it looks
       like a real title, not just a bare domain/path)
    2. Fetch the remote page ``<title>`` tag (best-effort, 3 s timeout)
       — all fetches run concurrently via ThreadPoolExecutor
    3. Derive a readable title from the URL path
    """
    seen: set[str] = set()
    ordered: list[tuple[str, str | None]] = []
    needs_fetch: list[str] = []

    for m in LINK_RE.finditer(html):
        url = m.group(1)
        if url in seen:
            continue
        seen.add(url)
        raw_text = TAG_RE.sub('', m.group(2)).strip()
        if raw_text and not _looks_like_url(raw_text):
            ordered.append((url, raw_text))
        else:
            ordered.append((url, None))
            needs_fetch.append(url)

    if needs_fetch:
        fetched: dict[str, str | None] = {}
        with ThreadPoolExecutor(max_workers=min(len(needs_fetch), 8)) as pool:
            future_to_url = {pool.submit(_fetch_page_title, url): url for url in needs_fetch}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    fetched[url] = future.result()
                except Exception:
                    fetched[url] = None

        ordered = [
            (url, title if title is not None else (fetched.get(url) or _title_from_url(url)))
            for url, title in ordered
        ]

    return [(url, title or _title_from_url(url)) for url, title in ordered]


def _looks_like_url(text: str) -> bool:
    """Return True if *text* looks like a bare URL or domain, not a title."""
    text = text.strip()
    if text.startswith(('http://', 'https://')):
        return True
    if '/' in text and '.' in text.split('/')[0]:
        return True
    if re.match(r'^[\w.-]+\.[a-z]{2,}', text, re.IGNORECASE):
        return True
    return False


def _fetch_page_title(url: str) -> str | None:
    """Best-effort fetch of the remote ``<title>`` tag (3 s timeout)."""
    try:
        with urlopen(url, timeout=3) as resp:  # noqa: S310
            chunk = resp.read(32_768).decode('utf-8', errors='replace')
        m = PAGE_TITLE_RE.search(chunk)
        if m:
            return unescape(m.group(1)).strip()
    except Exception:
        pass
    return None


def _title_from_url(url: str) -> str:
    """Last-resort: derive a short title from the URL path."""
    path = re.sub(r'^https?://(?:www\.)?', '', url).rstrip('/')
    last_segment = path.rsplit('/', 1)[-1] if '/' in path else path
    last_segment = re.sub(r'[-_]+', ' ', last_segment)
    return last_segment.title() if last_segment else path


def extract_accent(html: str) -> str:
    """Read the ``--accent`` CSS custom property value from the ``<style>`` block."""
    m = ACCENT_RE.search(html)
    return m.group(1) if m else "#29B5E8"


def make_qr_svg(url: str) -> str:
    """Generate an inline SVG string for *url* using segno.

    QR codes use black modules on a white background for maximum
    scan-ability regardless of the surrounding slide theme.

    Segno outputs ``width`` / ``height`` but no ``viewBox``, so the
    SVG can't scale.  We extract the native dimensions, add a
    ``viewBox``, then replace width/height with 100% so the code
    fills whatever container it's placed in.
    """
    qr = segno.make(url)
    buf = BytesIO()
    qr.save(
        buf,
        kind="svg",
        dark="#000000",
        light="#ffffff",
        border=2,
        xmldecl=False,
        svgns=False,
    )
    svg = buf.getvalue().decode("utf-8")
    w_match = re.search(r'width="(\d+)"', svg)
    h_match = re.search(r'height="(\d+)"', svg)
    vb_w = w_match.group(1) if w_match else "33"
    vb_h = h_match.group(1) if h_match else "33"
    svg = re.sub(r'\bwidth="[^"]*"', "", svg, count=1)
    svg = re.sub(r'\bheight="[^"]*"', "", svg, count=1)
    svg = re.sub(
        r"<svg\b([^>]*)>",
        rf'<svg\1 viewBox="0 0 {vb_w} {vb_h}" width="100%" height="100%" style="display:block;border-radius:8px;">',
        svg,
        count=1,
    )
    return svg


QR_PER_SLIDE = 6


def build_appendix_slide(
    links: list[tuple[str, str]], accent: str, slide_num: int,
    page_label: str = "",
) -> str:
    """Build the full HTML for one appendix slide (max QR_PER_SLIDE links)."""
    cards: list[str] = []
    for url, title in links:
        svg = make_qr_svg(url)
        card = (
            f'      <div style="background:rgba(255,255,255,0.04);border-radius:16px;'
            f'padding:24px;text-align:center;width:260px;">\n'
            f'        <div style="width:220px;height:220px;margin:0 auto;">\n'
            f"          {svg}\n"
            f'        </div>\n'
            f'        <p style="font-size:14px;color:#ccc;'
            f'margin-top:14px;line-height:1.3;">'
            f'<a href="{url}" target="_blank" rel="noopener" '
            f'style="border-bottom:none;color:#ccc;">{title}</a></p>\n'
            f"      </div>"
        )
        cards.append(card)

    cards_html = "\n".join(cards)
    heading = f"Resources{page_label}"

    slide = (
        f'\n<!-- Slide {slide_num}: Links (Appendix) -->\n'
        f'<div class="slide" id="s{slide_num}">\n'
        f'  <div class="slide-inner">\n'
        f'    <h2 class="anim">{heading}</h2>\n'
        f'    <p class="anim" style="font-size:16px;color:#666;margin-bottom:28px;'
        f'transition-delay:0.1s;">Scan to open</p>\n'
        f'    <div class="anim" style="display:flex;flex-wrap:wrap;justify-content:center;'
        f'gap:24px;transition-delay:0.2s;">\n'
        f"{cards_html}\n"
        f"    </div>\n"
        f"  </div>\n"
        f'  <div class="speaker-notes">Appendix: QR codes for all links referenced in '
        f"this presentation.</div>\n"
        f"</div>\n"
    )
    return slide


def remove_existing_appendix(html: str) -> tuple[str, int]:
    """Remove all existing QR appendix slides and return the cleaned HTML.

    Also returns the number of slides that were removed so the total counter
    can be adjusted.

    Args:
        html: The full deck HTML string.

    Returns:
        A tuple of (cleaned_html, slides_removed).
    """
    appendix_slide_re = re.compile(
        r'\n?<!-- Slide \d+: Links \(Appendix\) -->.*?(?=\n?<!-- Slide|\n?<div\s+class="counter")',
        re.DOTALL | re.IGNORECASE,
    )
    html, removed_count = appendix_slide_re.subn("", html)
    return html, removed_count


def find_last_slide_num(html: str) -> int:
    """Return the highest numeric slide ID found in the deck."""
    nums = [int(m.group(1)) for m in SLIDE_ID_RE.finditer(html)]
    return max(nums) if nums else 0


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Append QR-code appendix slide(s) to an HTML presentation."
    )
    parser.add_argument("html_file", help="Path to the HTML deck file")
    parser.add_argument(
        "--force", action="store_true",
        help="Remove and regenerate any existing QR appendix slide(s)"
    )
    args = parser.parse_args()

    html_path = Path(args.html_file).resolve()
    if not html_path.is_file():
        print(f"Error: File not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    html = html_path.read_text(encoding="utf-8")

    links = extract_links(html)
    if not links:
        print("No external links found — nothing to do.", file=sys.stderr)
        sys.exit(0)

    existing_appendix = re.search(
        r'<!-- Slide \d+: Links \(Appendix\) -->', html
    )
    if existing_appendix:
        if not args.force:
            print("QR appendix slide already exists — skipping. Use --force to regenerate.", file=sys.stderr)
            sys.exit(0)
        print("--force: removing existing QR appendix slide(s)...", file=sys.stderr)
        html, removed = remove_existing_appendix(html)
        if removed:
            num_match = re.search(r'<span\s+id="total">(\d+)</span>', html)
            if num_match:
                old_total = int(num_match.group(1))
                new_total = old_total - removed
                html = TOTAL_RE.sub(rf"\g<1>{new_total}\2", html)
            print(f"  Removed {removed} appendix slide(s).", file=sys.stderr)

    accent = extract_accent(html)
    last_num = find_last_slide_num(html)

    chunks = [links[i:i + QR_PER_SLIDE] for i in range(0, len(links), QR_PER_SLIDE)]
    total_pages = len(chunks)

    all_slides_html = ""
    for page_idx, chunk in enumerate(chunks):
        slide_num = last_num + 1 + page_idx
        page_label = f" ({page_idx + 1}/{total_pages})" if total_pages > 1 else ""
        all_slides_html += build_appendix_slide(chunk, accent, slide_num, page_label)

    counter_match = COUNTER_RE.search(html)
    if not counter_match:
        print("Error: Could not find <div class=\"counter\"> in the HTML.", file=sys.stderr)
        sys.exit(1)

    insert_pos = counter_match.start()
    html = html[:insert_pos] + all_slides_html + "\n" + html[insert_pos:]

    new_total = last_num + total_pages
    html = TOTAL_RE.sub(rf"\g<1>{new_total}\2", html)

    html_path.write_text(html, encoding="utf-8")
    print(
        f"Added {total_pages} QR appendix slide(s) "
        f"(s{last_num + 1}{'–s' + str(new_total) if total_pages > 1 else ''}) "
        f"with {len(links)} QR code(s).",
        file=sys.stderr,
    )
    print(f"  Accent color: {accent}", file=sys.stderr)
    for url, title in links:
        print(f"  • {title} → {url}", file=sys.stderr)


if __name__ == "__main__":
    main()
