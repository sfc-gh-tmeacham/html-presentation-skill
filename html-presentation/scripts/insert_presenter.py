#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "Pillow>=9.0",
# ]
# ///
"""Insert a presenter slide into an existing slide deck HTML file.

Automates the full pipeline: resize headshot images, convert to base64,
generate the presenter slide HTML (single or multi-presenter), inject it
after the Agenda slide, renumber all subsequent slide IDs, and update the
slide total counter.

Requires Pillow (installed automatically when invoked via run_script.py).
Requires: Pillow >= 9.1.0

Usage::

    python run_script.py insert_presenter.py <deck.html> \
        --name "Jane Doe" --title "VP Engineering" [--photo headshot.png] \
        [--name "John Smith" --title "CTO" [--photo john.png]]

Multiple presenters are supported by repeating --name/--title/--photo groups.
The --photo flag is optional per presenter; a Material Icon placeholder is
used when omitted.

Examples::

    # Single presenter with headshot
    python run_script.py insert_presenter.py slides.html \
        --name "Tom Meacham" --title "Principal Solution Engineer" \
        --photo ~/Downloads/tom.jpeg

    # Two presenters, one without a photo
    python run_script.py insert_presenter.py slides.html \
        --name "Alice" --title "CEO" --photo alice.png \
        --name "Bob" --title "CTO"
"""
# requires Python 3.10+

import base64
import mimetypes
import os
import re
import stat
import sys
import tempfile
from html import escape
from io import BytesIO
from pathlib import Path

mimetypes.add_type("image/svg+xml", ".svg")

try:
    from PIL import Image
except ImportError:
    Image = None


class InsertPresenterError(Exception):
    pass


def _fail(message: str, hint: str = "") -> int:
    """Print a structured ERROR (and optional HINT) to stderr and return exit code 1."""
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(f"HINT:  {hint}", file=sys.stderr)
    return 1


HEADSHOT_SIZE_CSS = "clamp(100px,12vmin,160px)"
HEADSHOT_ICON_CLAMP = "clamp(3rem,5vw,4.5rem)"
HEADSHOT_SIZE_CSS_MULTI = "clamp(80px,10vmin,140px)"
HEADSHOT_ICON_CLAMP_MULTI = "clamp(2rem,4vw,3.5rem)"

FORMAT_TO_MIME = {
    "JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif",
    "WEBP": "image/webp", "BMP": "image/bmp", "SVG": "image/svg+xml",
}


def resize_image(path: str, max_size: int = 300) -> bytes:
    """Resize an image to fit within max_size and return raw bytes.

    Args:
        path: Path to the source image file.
        max_size: Maximum dimension (width or height) in pixels.

    Returns:
        The resized image as bytes in its original format.

    Raises:
        InsertPresenterError: If Pillow is not installed or the file cannot be opened.
    """
    if Image is None:
        raise InsertPresenterError("Error: Pillow is required for image resizing. Install with: pip install Pillow")

    Image.MAX_IMAGE_PIXELS = 50_000_000

    try:
        img = Image.open(path)
        img.load()
    except Exception as exc:
        raise InsertPresenterError(f"Error: Cannot open image '{path}': {exc}")

    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    buf = BytesIO()
    fmt = img.format or "PNG"
    if fmt.upper() == "JPEG":
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
    img.save(buf, format=fmt)
    return buf.getvalue()


def image_to_base64(path: str, max_size: int = 300) -> str:
    """Convert an image file to a base64 data URI, resizing if needed.

    Args:
        path: Path to the image file (PNG, JPG, SVG, etc.).
        max_size: Maximum dimension for raster images.

    Returns:
        A complete ``data:<mime>;base64,...`` URI string.
    """
    ext = Path(path).suffix.lower()
    guessed_mime = mimetypes.guess_type(path)[0]

    if ext == ".svg":
        with open(path, "rb") as f:
            raw = f.read()
        mime = guessed_mime or "image/svg+xml"
    else:
        raw = resize_image(path, max_size)
        if Image is not None:
            try:
                img = Image.open(BytesIO(raw))
                mime = FORMAT_TO_MIME.get(img.format, guessed_mime or "image/png")
            except Exception:
                mime = guessed_mime or "image/png"
        else:
            mime = guessed_mime or "image/png"

    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def build_headshot_html(name: str, b64: str | None, size_css: str, icon_clamp: str) -> str:
    """Build the HTML for a single presenter's headshot element.

    Args:
        name: Presenter name (used for alt text).
        b64: Base64 data URI for the photo, or None for placeholder.
        size_css: CSS clamp() value for width/height (e.g. 'clamp(100px,12vmin,160px)').
        icon_clamp: CSS clamp() value for the placeholder icon font-size.

    Returns:
        An HTML string for the headshot (img tag or icon placeholder).
    """
    circle_style = (
        f"width:{size_css};height:{size_css};border-radius:50%;"
        f"object-fit:cover;border:3px solid var(--accent);"
    )
    if b64:
        return (
            f'<img src="{b64}" alt="{escape(name)}" style="{circle_style}">'
        )
    return (
        f'<div style="{circle_style}display:flex;align-items:center;'
        f'justify-content:center;background:var(--card);">'
        f'<span class="material-symbols-rounded" '
        f'style="font-size:{icon_clamp};color:var(--accent);">person</span>'
        f'</div>'
    )


def build_presenter_slide(presenters: list[dict]) -> str:
    """Generate the full presenter slide HTML.

    Args:
        presenters: List of dicts with keys 'name', 'title', and optional 'b64'.

    Returns:
        Complete HTML for the presenter slide div.
    """
    count = len(presenters)

    if count == 1:
        p = presenters[0]
        headshot = build_headshot_html(
            p["name"], p.get("b64"),
            HEADSHOT_SIZE_CSS, HEADSHOT_ICON_CLAMP,
        )
        return (
            '<!-- Presenter Slide -->\n'
            '<div class="slide" id="s_presenter">\n'
            '  <div class="slide-inner">\n'
            '    <h3 class="anim" style="font-size:1rem;text-transform:uppercase;'
            'letter-spacing:2px;color:var(--accent);margin-bottom:32px;">'
            'Presented By</h3>\n'
            '    <div class="anim" style="display:flex;flex-direction:column;'
            'align-items:center;gap:16px;transition-delay:0.1s;">\n'
            f'      {headshot}\n'
            '      <div style="text-align:center;">\n'
            f'        <h4 style="font-size:clamp(1.5rem,2.5vw,2.25rem);margin-bottom:4px;">{escape(p["name"])}</h4>\n'
            f'        <p style="font-size:clamp(1rem,1.5vw,1.5rem);color:var(--secondary);">{escape(p["title"])}</p>\n'
            '      </div>\n'
            '    </div>\n'
            '  </div>\n'
            '</div>\n'
        )

    cols = 2 if count <= 4 else 3
    cards = []
    for p in presenters:
        headshot = build_headshot_html(
            p["name"], p.get("b64"),
            HEADSHOT_SIZE_CSS_MULTI, HEADSHOT_ICON_CLAMP_MULTI,
        )
        cards.append(
            f'    <div class="card" style="text-align:center;padding:28px 24px;">\n'
            f'      {headshot}\n'
            f'      <h4 style="font-size:clamp(1.1rem,2vw,1.5rem);margin-top:12px;margin-bottom:4px;">{escape(p["name"])}</h4>\n'
            f'      <p style="font-size:clamp(0.875rem,1.3vw,1.125rem);color:var(--secondary);">{escape(p["title"])}</p>\n'
            f'    </div>'
        )
    cards_html = "\n".join(cards)
    heading = "Your Presenters"

    return (
        '<!-- Presenter Slide -->\n'
        '<div class="slide" id="s_presenter">\n'
        '  <div class="slide-inner">\n'
        f'    <h3 class="anim" style="font-size:1rem;text-transform:uppercase;'
        f'letter-spacing:2px;color:var(--accent);margin-bottom:32px;">'
        f'{heading}</h3>\n'
        f'    <div class="card-grid anim stagger" style="grid-template-columns:'
        f'repeat({cols},1fr);gap:24px;transition-delay:0.1s;">\n'
        f'{cards_html}\n'
        f'    </div>\n'
        '  </div>\n'
        '</div>\n'
    )


def find_insertion_point(html: str) -> str | None:
    """Find the HTML comment to insert the presenter slide before.

    Searches for the insertion marker in this priority order:

    1. ``<!-- Slide 2: ... -->`` only if it mentions "agenda"
    2. ``<!-- Slide N: Agenda ... -->`` for any slide N
    3. ``<!-- Slide N: ... -->`` for any N >= 2

    For standard decks (Title slide followed immediately by Agenda), the
    presenter slide ends up right after the Title slide. For non-standard
    layouts (e.g. Title → Company Overview → Agenda), insertion happens
    before the first Agenda slide found, which may not be Slide 2. If no
    Agenda slide exists, insertion falls back to the first non-title slide
    (N >= 2).

    Args:
        html: The full deck HTML string.

    Returns:
        The matched comment string, or None if not found.
    """
    for i, pattern_str in enumerate([r'<!-- Slide 2:.*?-->', r'<!-- Slide \d+:\s*Agenda.*?-->', r'<!-- Slide (?:[2-9]|\d{2,}):.*?-->']):
        match = re.search(pattern_str, html, re.DOTALL)
        if match:
            if i == 0 and 'agenda' not in match.group(0).lower():
                continue
            return match.group(0)
    return None


def find_total_span(html: str) -> int | None:
    """Extract the current total from the ``<span id="total">`` element.

    Args:
        html: The full deck HTML string.

    Returns:
        The current total number, or None if not found.
    """
    match = re.search(r'<span id="total">(\d+)</span>', html)
    if match:
        return int(match.group(1))
    return None


def insert_slide(html: str, presenter_html: str) -> str:
    """Insert the presenter slide and renumber all subsequent slides.

    Args:
        html: The full deck HTML string.
        presenter_html: The generated presenter slide HTML.

    Returns:
        The modified HTML with the presenter slide inserted.

    Raises:
        InsertPresenterError: If the insertion point or slide IDs cannot be found.
    """
    insertion_comment = find_insertion_point(html)
    if not insertion_comment:
        raise InsertPresenterError("Error: Could not find a <!-- Slide N: ... --> comment to insert before.")

    slide_num_match = re.search(r'Slide (\d+)', insertion_comment)
    if not slide_num_match:
        raise InsertPresenterError("Error: Could not parse slide number from insertion comment.")
    first_slide_num = int(slide_num_match.group(1))
    current_total = find_total_span(html)

    html = html.replace(
        insertion_comment,
        presenter_html + "\n" + insertion_comment,
        1,
    )

    html = re.sub(
        r'(<div\s[^>]*(?<![a-zA-Z0-9_-])id="s)(\d+)(")',
        lambda m: f'{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}' if int(m.group(2)) >= first_slide_num else m.group(0),
        html,
    )

    html = re.sub(
        r'(<div\s[^>]*\bid=")s_presenter(")',
        rf'\g<1>s{first_slide_num}\2',
        html,
    )

    if current_total is not None:
        new_total = current_total + 1
        html = html.replace(
            f'<span id="total">{current_total}</span>',
            f'<span id="total">{new_total}</span>',
            1,
        )

    return html


def parse_presenters(args: list[str]) -> tuple[str, list[dict]]:
    """Parse command-line arguments into the deck path and presenter list.

    Args:
        args: Raw sys.argv[1:] arguments.

    Returns:
        A tuple of (deck_path, presenters_list).

    Raises:
        InsertPresenterError: On invalid arguments.
    """
    if not args or args[0].startswith("-"):
        raise InsertPresenterError(
            "Usage: insert_presenter.py <deck.html> "
            "--name NAME --title TITLE [--photo FILE] [...]"
        )

    deck_path = args[0]
    if not Path(deck_path).is_file():
        raise InsertPresenterError(f"Deck file not found: {deck_path}")

    presenters = []
    current = {}
    i = 1
    while i < len(args):
        arg = args[i]
        if arg in ("--name", "--title", "--photo") and i + 1 >= len(args):
            raise InsertPresenterError(f"{arg} requires a value")
        if arg == "--name":
            if current.get("name"):
                presenters.append(current)
                current = {}
            value = args[i + 1].strip()
            if not value:
                raise InsertPresenterError("--name value cannot be empty")
            current["name"] = value
            i += 2
        elif arg == "--title":
            if "name" not in current:
                raise InsertPresenterError("--title must follow --name")
            value = args[i + 1].strip()
            if not value:
                raise InsertPresenterError("--title value cannot be empty")
            current["title"] = value
            i += 2
        elif arg == "--photo":
            current["photo"] = args[i + 1]
            i += 2
        else:
            raise InsertPresenterError(f"Unknown argument: {arg}")

    if current.get("name"):
        presenters.append(current)

    if not presenters:
        raise InsertPresenterError("At least one --name/--title pair is required.")

    MAX_PRESENTERS = 9
    if len(presenters) > MAX_PRESENTERS:
        raise InsertPresenterError(
            f"Maximum {MAX_PRESENTERS} presenters supported, got {len(presenters)}"
        )

    for p in presenters:
        if "title" not in p:
            raise InsertPresenterError(f"Missing --title for presenter '{p['name']}'")

    return deck_path, presenters


def main() -> int:
    """Parse arguments, process images, build and insert the presenter slide."""
    try:
        deck_path, presenters = parse_presenters(sys.argv[1:])
    except InsertPresenterError as exc:
        return _fail(
            str(exc),
            "Usage: insert_presenter.py <deck.html> --name NAME --title TITLE [--photo FILE] [...]",
        )

    try:
        for p in presenters:
            if "photo" in p:
                photo_path = os.path.expanduser(p["photo"])
                if not Path(photo_path).is_file():
                    print(f"Warning: Photo not found '{photo_path}', using placeholder.", file=sys.stderr)
                else:
                    p["b64"] = image_to_base64(photo_path)

        presenter_html = build_presenter_slide(presenters)

        try:
            with open(deck_path, encoding="utf-8") as f:
                html = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            return _fail(
                f"Cannot read '{deck_path}': {exc}",
                "Ensure the deck file exists and is valid UTF-8.",
            )

        html = insert_slide(html, presenter_html)

        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=Path(deck_path).parent, prefix=".presenter_tmp_", suffix=".html"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(html)
            tmp_fd = None
            orig_mode = Path(deck_path).stat().st_mode
            os.chmod(tmp_path, stat.S_IMODE(orig_mode))
            os.replace(tmp_path, deck_path)
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
                f"Could not write '{deck_path}': {exc}",
                "Check that the deck directory is writable.",
            )

        names = ", ".join(p["name"] for p in presenters)
        total_val = find_total_span(html)
        total = str(total_val) if total_val is not None else "?"
        print(f"SUCCESS: Inserted presenter slide ({names}) | {total} slides total | deck: {deck_path}")
        print(f"NEXT: Run validate_deck.py to verify the updated deck.")
        return 0

    except InsertPresenterError as exc:
        return _fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
