#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "segno>=1.0",
# ]
# ///
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

import argparse
import ipaddress
import os
import re
import socket
import sys
import tempfile
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape, unescape
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from urllib.request import build_opener, HTTPRedirectHandler, Request

try:
    import segno
except ImportError:
    print(
        "Error: 'segno' is not installed.  "
        "Run this script via run_script.py to auto-install dependencies.",
        file=sys.stderr,
    )
    sys.exit(1)

MAX_FETCH_WORKERS = 8
_TITLE_FETCH_CHUNK_BYTES = 32_768
_TITLE_FETCH_TIMEOUT_S = 3
_MAX_DECK_FILE_BYTES = 10 * 1024 * 1024

LINK_RE = re.compile(
    r'<a\s[^>]*href=(?:"(https?://[^"]+)"|\'(https?://[^\']+)\')[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r'<[^>]+>')
PAGE_TITLE_RE = re.compile(r'<title[^>]*>([^<]+)</title>', re.IGNORECASE)
ACCENT_RE = re.compile(r"--accent:\s*(#[0-9A-Fa-f]{3,8})\s*;")
TOTAL_RE = re.compile(r'(<span\s+id="total">)\d+(</span>)')
COUNTER_RE = re.compile(r'<div\s+class="counter"')
SLIDE_ID_RE = re.compile(r'<div\b[^>]*?\bid="s(\d+)"', re.IGNORECASE)
APPENDIX_SLIDE_RE = re.compile(
    r'\n?<!-- Slide \d+: Links \(Appendix\) -->.*?(?=\n?<!-- Slide|\n?<div\s+class="counter")',
    re.DOTALL | re.IGNORECASE,
)
_DOMAIN_RE = re.compile(r'^[\w.-]+\.[a-z]{2,}', re.IGNORECASE)
_HTTP_PREFIX_RE = re.compile(r'^https?://(?:www\.)?')
_SLUG_SEP_RE = re.compile(r'[-_]+')
_QR_WIDTH_RE = re.compile(r'width="(\d+)"')
_QR_HEIGHT_RE = re.compile(r'height="(\d+)"')
_QR_WIDTH_ATTR_RE = re.compile(r'\bwidth="[^"]*"')
_QR_HEIGHT_ATTR_RE = re.compile(r'\bheight="[^"]*"')
_QR_SVG_OPEN_TAG_RE = re.compile(r'<svg\b([^>]*)>')
_APPENDIX_MARKER_RE = re.compile(r'<!-- Slide \d+: Links \(Appendix\) -->')
_SLIDE_TOTAL_RE = re.compile(r'<span\s+id="total">(\d+)</span>')
_APPENDIX_BLOCK_RE = re.compile(
    r'<!-- Slide \d+: Links \(Appendix\) -->',
    re.IGNORECASE,
)

_PRIVATE_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "Redirect blocked (SSRF guard)", headers, fp)


_SAFE_OPENER = build_opener(_NoRedirect())


def extract_links(html: str, fetch_titles: bool = False) -> list[tuple[str, str]]:
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
        url = m.group(1) or m.group(2)
        if url in seen:
            continue
        seen.add(url)
        raw_text = TAG_RE.sub('', m.group(3)).strip()
        if raw_text and not _looks_like_url(raw_text):
            ordered.append((url, raw_text))
        else:
            ordered.append((url, None))
            if fetch_titles:
                needs_fetch.append(url)

    if fetch_titles and needs_fetch:
        print(f"Fetching titles for {len(needs_fetch)} URL(s)...", file=sys.stderr)
        fetched: dict[str, str | None] = {}
        with ThreadPoolExecutor(max_workers=min(len(needs_fetch), MAX_FETCH_WORKERS)) as pool:
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
    if _DOMAIN_RE.match(text):
        return True
    return False


def _fetch_page_title(url: str) -> str | None:
    """Best-effort fetch of the remote ``<title>`` tag (3 s timeout)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return None
    # Single resolution — reuse same IP for both check and connect
    try:
        resolved_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        return None
    ip_obj = ipaddress.ip_address(resolved_ip)
    if any(ip_obj in net for net in _PRIVATE_NETWORKS):
        return None
    # Build a URL pointing at the resolved IP directly; pass Host header
    port = parsed.port
    netloc_ip = (
        f"[{resolved_ip}]:{port}" if ":" in resolved_ip
        else (f"{resolved_ip}:{port}" if port else resolved_ip)
    )
    ip_url = urlunparse(parsed._replace(netloc=netloc_ip))
    req = Request(ip_url, headers={"Host": hostname, "User-Agent": "Mozilla/5.0"})
    try:
        with _SAFE_OPENER.open(req, timeout=_TITLE_FETCH_TIMEOUT_S) as resp:
            chunk = resp.read(_TITLE_FETCH_CHUNK_BYTES).decode('utf-8', errors='replace')
        m = PAGE_TITLE_RE.search(chunk)
        if m:
            return unescape(m.group(1)).strip()
    except Exception:
        pass
    return None


def _title_from_url(url: str) -> str:
    """Last-resort: derive a short title from the URL path."""
    path = _HTTP_PREFIX_RE.sub('', url).rstrip('/')
    last_segment = path.rsplit('/', 1)[-1] if '/' in path else path
    last_segment = _SLUG_SEP_RE.sub(' ', last_segment)
    name = last_segment.removeprefix("www.")
    return name or url


def extract_accent(html: str) -> str:
    """Read the ``--accent`` CSS custom property value from the ``<style>`` block."""
    m = ACCENT_RE.search(html)
    return m.group(1) if m else "#29B5E8"


def make_qr_svg(url: str) -> str | None:
    """Generate an inline SVG string for *url* using segno.

    QR codes use black modules on a white background for maximum
    scan-ability regardless of the surrounding slide theme.

    Segno outputs ``width`` / ``height`` but no ``viewBox``, so the
    SVG can't scale.  We extract the native dimensions, add a
    ``viewBox``, then replace width/height with 100% so the code
    fills whatever container it's placed in.
    """
    if len(url.encode()) > 2953:
        print(
            f"Warning: URL too long for QR generation ({len(url.encode())} bytes): {url!r}",
            file=sys.stderr,
        )
        return None
    try:
        qr = segno.make(url)
    except Exception as exc:
        print(f"Warning: QR generation failed for {url!r}: {exc}", file=sys.stderr)
        return None
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
    w_match = _QR_WIDTH_RE.search(svg)
    h_match = _QR_HEIGHT_RE.search(svg)
    vb_w = w_match.group(1) if w_match else "33"  # 33 is segno's minimum QR module size (1-M, border=0)
    vb_h = h_match.group(1) if h_match else "33"  # 33 is segno's minimum QR module size (1-M, border=0)
    if not _QR_SVG_OPEN_TAG_RE.search(svg):
        print(f"Warning: malformed SVG from segno for {url!r}", file=sys.stderr)
        return None
    svg = _QR_WIDTH_ATTR_RE.sub("", svg)
    svg = _QR_HEIGHT_ATTR_RE.sub("", svg)
    svg = _QR_SVG_OPEN_TAG_RE.sub(
        rf'<svg\1 viewBox="0 0 {vb_w} {vb_h}" width="100%" height="100%" style="display:block;border-radius:8px;">',
        svg,
        count=1,
    )
    return svg


QR_PER_SLIDE = 6


def build_appendix_slide(
    links: list[tuple[str, str]], slide_num: int,
    page_label: str = "",
) -> tuple[str, int] | None:
    """Build the full HTML for one appendix slide (max QR_PER_SLIDE links).

    Returns a ``(slide_html, card_count)`` tuple, or ``None`` if every QR code
    in this chunk failed to generate.
    """
    cards: list[str] = []
    for url, title in links:
        svg = make_qr_svg(url)
        if svg is None:
            print(f"Warning: skipping link {url!r} — QR generation returned None", file=sys.stderr)
            continue
        card = (
            f'      <div style="background:rgba(255,255,255,0.04);border-radius:16px;'
            f'padding:1.5rem;text-align:center;width:16.25rem;">\n'
            f'        <div style="width:13.75rem;height:13.75rem;margin:0 auto;">\n'
            f"          {svg}\n"
            f'        </div>\n'
            f'        <p style="font-size:0.875rem;color:#ccc;'
            f'margin-top:0.875rem;line-height:1.3;">'
            f'<a href="{escape(url)}" target="_blank" rel="noopener" '
            f'style="border-bottom:none;color:#ccc;">{escape(title)}</a></p>\n'
            f"      </div>"
        )
        cards.append(card)

    if not cards:
        return None

    cards_html = "\n".join(cards)
    heading = f"Resources{page_label}"

    slide = (
        f'\n<!-- Slide {slide_num}: Links (Appendix) -->\n'
        f'<div id="s{slide_num}" class="slide">\n'
        f'  <div class="slide-inner">\n'
        f'    <h2 class="anim">{heading}</h2>\n'
        f'    <p class="anim" style="font-size:1rem;color:#666;margin-bottom:1.75rem;'
        f'transition-delay:0.1s;">Scan to open</p>\n'
        f'    <div class="anim" style="display:flex;flex-wrap:wrap;justify-content:center;'
        f'gap:1.5rem;transition-delay:0.2s;">\n'
        f"{cards_html}\n"
        f"    </div>\n"
        f"  </div>\n"
        f'  <div class="speaker-notes">Appendix: QR codes for all links referenced in '
        f"this presentation.</div>\n"
        f"</div>\n"
    )
    return slide, len(cards)


def remove_existing_appendix(html: str) -> tuple[str, int]:
    """Remove all existing QR appendix slides and return the cleaned HTML.

    Also returns the number of slides that were removed so the total counter
    can be adjusted.

    Args:
        html: The full deck HTML string.

    Returns:
        A tuple of (cleaned_html, slides_removed).
    """
    if len(html.encode('utf-8')) > _MAX_DECK_FILE_BYTES:
        print(
            "Warning: file exceeds 10 MB; skipping appendix removal regex to avoid ReDoS.",
            file=sys.stderr,
        )
        return html, 0
    html, removed_count = APPENDIX_SLIDE_RE.subn("", html)
    return html, removed_count


def find_last_slide_num(html: str) -> int:
    """Return the highest numeric slide ID found in the deck."""
    nums = [int(m.group(1)) for m in SLIDE_ID_RE.finditer(html)]
    if not nums and html.strip():
        print("Warning: no slide IDs found in non-empty deck.", file=sys.stderr)
    return max(nums) if nums else 0


def _fail(message: str, hint: str = "") -> int:
    """Print a structured ERROR (and optional HINT) to stderr and return exit code 1."""
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(f"HINT:  {hint}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append QR-code appendix slide(s) to an HTML presentation."
    )
    parser.add_argument("html_file", help="Path to the HTML deck file")
    parser.add_argument(
        "--force", action="store_true",
        help="Remove and regenerate any existing QR appendix slide(s)"
    )
    parser.add_argument(
        "--fetch-titles", action="store_true",
        help="Fetch page titles from remote URLs (makes HTTP requests)"
    )
    args = parser.parse_args()

    html_path = Path(args.html_file).resolve()
    if not html_path.is_file():
        return _fail(
            f"File not found: {html_path}",
            "Check the path and ensure the deck file exists.",
        )

    try:
        html = html_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return _fail(
            f"Could not read '{html_path}': {exc}",
            "Ensure the file is readable and encoded as UTF-8.",
        )

    links = extract_links(html, fetch_titles=args.fetch_titles)
    if not links:
        print(f"SUCCESS: No external links found in '{html_path.name}' — nothing to do.")
        print(f"NEXT: Run validate_deck.py to verify the deck.")
        return 0

    existing_appendix = _APPENDIX_MARKER_RE.search(html)
    if existing_appendix:
        if not args.force:
            print(f"SUCCESS: QR appendix already exists in '{html_path.name}' — skipped (use --force to regenerate).")
            return 0
        print("--force: removing existing QR appendix slide(s)...", file=sys.stderr)
        html, removed = remove_existing_appendix(html)
        if removed:
            num_match = _SLIDE_TOTAL_RE.search(html)
            if num_match:
                old_total = int(num_match.group(1))
                new_total = old_total - removed
                html = TOTAL_RE.sub(rf"\g<1>{new_total}\2", html)
            print(f"  Removed {removed} appendix slide(s).", file=sys.stderr)

    last_num = find_last_slide_num(html)

    chunks = [links[i:i + QR_PER_SLIDE] for i in range(0, len(links), QR_PER_SLIDE)]
    total_pages = len(chunks)

    slides_parts: list[str] = []
    actual_slides = 0
    actual_cards = 0
    for page_idx, chunk in enumerate(chunks):
        slide_num = last_num + 1 + actual_slides
        page_label = f" ({page_idx + 1}/{total_pages})" if total_pages > 1 else ""
        result = build_appendix_slide(chunk, slide_num, page_label)
        if result is None:
            continue
        slide_html, card_count = result
        slides_parts.append(slide_html)
        actual_slides += 1
        actual_cards += card_count
    all_slides_html = ''.join(slides_parts)

    counter_match = COUNTER_RE.search(html)
    if not counter_match:
        return _fail(
            "Could not find <div class=\"counter\"> in the HTML.",
            "Ensure the deck was generated by this skill and contains the standard counter element.",
        )

    insert_pos = counter_match.start()
    html = html[:insert_pos] + all_slides_html + "\n" + html[insert_pos:]

    total_match = _SLIDE_TOTAL_RE.search(html)
    current_total = int(total_match.group(1)) if total_match else last_num
    new_total = current_total + actual_slides
    html = TOTAL_RE.sub(rf"\g<1>{new_total}\2", html)

    tmp_fd, tmp_path = None, None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=html_path.parent, prefix=".qr_tmp_", suffix=".html"
        )
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(html)
        tmp_fd = None
        os.replace(tmp_path, html_path)
        tmp_path = None
    except OSError as exc:
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return _fail(
            f"Could not write '{html_path}': {exc}",
            "Check that the deck directory is writable.",
        )

    slide_range = f"s{last_num + 1}"
    if actual_slides > 1:
        slide_range += f"–s{last_num + actual_slides}"
    print(
        f"SUCCESS: Added {actual_slides} QR appendix slide(s) ({slide_range}) "
        f"with {actual_cards} QR code(s) | deck: {html_path.name}"
    )
    for url, title in links:
        print(f"  • {title} → {url}", file=sys.stderr)
    print(f"NEXT: Run validate_deck.py to verify the final deck.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
