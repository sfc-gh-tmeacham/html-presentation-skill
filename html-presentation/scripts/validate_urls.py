#!/usr/bin/env python3
"""Check that every external URL in a file resolves with HTTP 200.

Works on two file types:

  * **Markdown / plain text** (e.g. a research brief) -- extracts bare URLs
    matching ``https?://...``
  * **HTML deck** -- extracts only ``href="https://..."`` link targets, skipping
    Google Fonts/API calls that are expected to require a browser context.

Prints one line per URL::

    200  https://example.com/page
    403* https://bot-protected.example.com  (likely bot protection)
    404  https://dead.example.com/gone
    ERR  https://timeout.example.com  <urlopen error ...>

Exit codes:
  0  all URLs returned 200 (or only 403-bot-blocked)
  1  one or more URLs returned non-200 or errored (excluding bot-blocked)
  2  usage / file-not-found error

Usage::

    python run_script.py validate_urls.py <file> [--mode auto|brief|html]

Options::

    --mode   Force detection mode.  ``auto`` (default) infers from file
             extension: ``.html``/``.htm`` → html, everything else → brief.
"""

import argparse
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

_SKIP_DOMAINS = frozenset({
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "ajax.googleapis.com",
})

_BRIEF_URL_RE = re.compile(r"https?://[^\s)>\"'\]]+")
_HTML_HREF_RE = re.compile(r'href="(https?://[^"]+)"')


def _skip(url: str) -> bool:
    return any(domain in url for domain in _SKIP_DOMAINS)


def extract_urls(text: str, mode: str) -> list[str]:
    if mode == "html":
        raw = _HTML_HREF_RE.findall(text)
    else:
        raw = _BRIEF_URL_RE.findall(text)
    seen: set[str] = set()
    result: list[str] = []
    for u in raw:
        u = u.rstrip(".,;)")
        if u not in seen and not _skip(u):
            seen.add(u)
            result.append(u)
    return sorted(result)


_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def check_url(url: str, timeout: int = 10) -> str:
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, headers=_BROWSER_HEADERS, method="HEAD")
        code = urllib.request.urlopen(req, timeout=timeout, context=ctx).status
        return str(code)
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            req = urllib.request.Request(url, headers=_BROWSER_HEADERS, method="GET")
            try:
                code = urllib.request.urlopen(req, timeout=timeout, context=ctx).status
                return str(code)
            except urllib.error.HTTPError as inner:
                return str(inner.code)
        if exc.code == 403:
            return "403-bot-blocked"
        return str(exc.code)
    except Exception as exc:
        return str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify that every external URL in a file resolves."
    )
    parser.add_argument("file", help="Path to the HTML deck or text/markdown file")
    parser.add_argument(
        "--mode",
        choices=["auto", "brief", "html"],
        default="auto",
        help="URL extraction mode (default: auto-detect from extension)",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"Error: '{path}' not found or not a file.", file=sys.stderr)
        sys.exit(2)

    mode = args.mode
    if mode == "auto":
        mode = "html" if path.suffix.lower() in {".html", ".htm"} else "brief"

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"Error: '{path}' is not valid UTF-8.", file=sys.stderr)
        sys.exit(2)

    urls = extract_urls(text, mode)
    if not urls:
        print(f"No external URLs found in '{path.name}' (mode: {mode}).")
        sys.exit(0)

    print(f"Checking {len(urls)} URL(s) in '{path.name}' (mode: {mode})...")
    failures: list[str] = []
    bot_blocked: list[str] = []
    for url in urls:
        result = check_url(url)
        if result == "403-bot-blocked":
            print(f"  403*  {url}  (likely bot protection — verify manually or use web_fetch)")
            bot_blocked.append(url)
        elif result != "200":
            print(f"  {result}  {url}")
            failures.append(url)
        else:
            print(f"  {result}  {url}")

    if bot_blocked:
        print(f"\n{len(bot_blocked)} URL(s) returned 403 (likely bot protection — not counted as failures).")
    if failures:
        print(f"\n{len(failures)} URL(s) returned non-200 — fix or remove them before proceeding.")
        sys.exit(1)
    else:
        print("\nAll URLs OK.")
        sys.exit(0)


if __name__ == "__main__":
    main()
