#!/usr/bin/env python3
"""Check that every external URL in a file resolves with HTTP 200.

Works on two file types:

  * **Markdown / plain text** (e.g. a research brief) -- extracts bare URLs
    matching ``https?://...``
  * **HTML deck** -- extracts only ``href="https://..."`` link targets, skipping
    Google Fonts/API calls that are expected to require a browser context.

Prints one line per URL::

    200  https://example.com/page
    404  https://dead.example.com/gone
    <urlopen error ...>  https://timeout.example.com

Exit codes:
  0  all URLs returned 200
  1  one or more URLs returned non-200 or errored
  2  usage / file-not-found error

Usage::

    python run_script.py validate_urls.py <file> [--mode auto|brief|html]

Options::

    --mode   Force detection mode.  ``auto`` (default) infers from file
             extension: ``.html``/``.htm`` → html, everything else → brief.
"""

import argparse
import re
import sys
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


def check_url(url: str, timeout: int = 10) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        code = urllib.request.urlopen(req, timeout=timeout).status
        return str(code)
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
    for url in urls:
        result = check_url(url)
        print(f"  {result}  {url}")
        if result != "200":
            failures.append(url)

    if failures:
        print(f"\n{len(failures)} URL(s) returned non-200 — fix or remove them before proceeding.")
        sys.exit(1)
    else:
        print("\nAll URLs OK.")
        sys.exit(0)


if __name__ == "__main__":
    main()
