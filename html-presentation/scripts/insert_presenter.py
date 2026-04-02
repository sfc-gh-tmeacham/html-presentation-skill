#!/usr/bin/env python3
"""Insert a presenter slide into an existing slide deck HTML file.

Automates the full pipeline: resize headshot images, convert to base64,
generate the presenter slide HTML (single or multi-presenter), inject it
after the Agenda slide, renumber all subsequent slide IDs, and update the
slide total counter.

Requires Pillow (installed automatically when invoked via run_script.py).

Usage::

    python run_script.py insert_presenter.py <deck.html> \\
        --name "Jane Doe" --title "VP Engineering" [--photo headshot.png] \\
        [--name "John Smith" --title "CTO" [--photo john.png]]

Multiple presenters are supported by repeating --name/--title/--photo groups.
The --photo flag is optional per presenter; a Material Icon placeholder is
used when omitted.

Examples::

    # Single presenter with headshot
    python run_script.py insert_presenter.py slides.html \\
        --name "Tom Meacham" --title "Principal Solution Engineer" \\
        --photo ~/Downloads/tom.jpeg

    # Two presenters, one without a photo
    python run_script.py insert_presenter.py slides.html \\
        --name "Alice" --title "CEO" --photo alice.png \\
        --name "Bob" --title "CTO"
"""

import base64
import mimetypes
import os
import re
import sys
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None


def resize_image(path: str, max_size: int = 300) -> bytes:
    """Resize an image to fit within max_size and return raw bytes.

    Args:
        path: Path to the source image file.
        max_size: Maximum dimension (width or height) in pixels.

    Returns:
        The resized image as bytes in its original format.

    Raises:
        SystemExit: If Pillow is not installed or the file cannot be opened.
    """
    if Image is None:
        print("Error: Pillow is required for image resizing.", file=sys.stderr)
        sys.exit(1)

    try:
        img = Image.open(path)
    except Exception as exc:
        print(f"Error: Cannot open image '{path}': {exc}", file=sys.stderr)
        sys.exit(1)

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
    mime = mimetypes.guess_type(path)[0] or "image/png"

    if ext == ".svg":
        with open(path, "rb") as f:
            raw = f.read()
    else:
        raw = resize_image(path, max_size)

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
            f'<img src="{b64}" alt="{name}" style="{circle_style}">'
        )
    return (
        f'<div style="{circle_style}display:flex;align-items:center;'
        f'justify-content:center;background:var(--card);">'
        f'<span class="material-icons-round" '
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
            "clamp(100px,12vmin,160px)", "clamp(3rem,5vw,4.5rem)",
        )
        return (
            '<!-- Presenter Slide -->\n'
            '<div class="slide" id="s_presenter">\n'
            '  <div class="slide-inner">\n'
            '    <h3 class="anim" style="font-size:16px;text-transform:uppercase;'
            'letter-spacing:2px;color:var(--accent);margin-bottom:32px;">'
            'Presented By</h3>\n'
            '    <div class="anim" style="display:flex;flex-direction:column;'
            'align-items:center;gap:16px;transition-delay:0.1s;">\n'
            f'      {headshot}\n'
            '      <div style="text-align:center;">\n'
            f'        <h4 style="font-size:clamp(1.5rem,2.5vw,2.25rem);margin-bottom:4px;">{p["name"]}</h4>\n'
            f'        <p style="font-size:clamp(1rem,1.5vw,1.5rem);color:var(--secondary);">{p["title"]}</p>\n'
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
            "clamp(80px,10vmin,140px)", "clamp(2rem,4vw,3.5rem)",
        )
        cards.append(
            f'    <div class="card" style="text-align:center;padding:28px 24px;">\n'
            f'      {headshot}\n'
            f'      <h4 style="font-size:clamp(1.1rem,2vw,1.5rem);margin-top:12px;margin-bottom:4px;">{p["name"]}</h4>\n'
            f'      <p style="font-size:clamp(0.875rem,1.3vw,1.125rem);color:var(--secondary);">{p["title"]}</p>\n'
            f'    </div>'
        )
    cards_html = "\n".join(cards)
    heading = "Your Presenters"

    return (
        '<!-- Presenter Slide -->\n'
        '<div class="slide" id="s_presenter">\n'
        '  <div class="slide-inner">\n'
        f'    <h3 class="anim" style="font-size:16px;text-transform:uppercase;'
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
    """Find the HTML comment or element immediately after the Title slide.

    The presenter slide is always inserted right after the Title slide
    (before the Agenda). Looks for ``<!-- Agenda`` or ``<!-- Slide 2:``
    as the marker to insert before.

    Args:
        html: The full deck HTML string.

    Returns:
        The matched comment string, or None if not found.
    """
    for pattern in [r'<!-- Agenda.*?-->', r'<!-- Slide 2:.*?-->']:
        match = re.search(pattern, html)
        if match:
            return match.group(0)
    match = re.search(r'<!-- Slide \d+:.*?-->', html)
    if match:
        return match.group(0)
    return None


def count_slides(html: str) -> int:
    """Count the number of slides by finding the highest slide ID.

    Args:
        html: The full deck HTML string.

    Returns:
        The highest slide number found.
    """
    ids = re.findall(r'id="s(\d+)"', html)
    if not ids:
        return 0
    return max(int(x) for x in ids)


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
        SystemExit: If the insertion point or slide IDs cannot be found.
    """
    insertion_comment = find_insertion_point(html)
    if not insertion_comment:
        print("Error: Could not find a <!-- Slide N: ... --> comment to insert before.", file=sys.stderr)
        sys.exit(1)

    slide_num_match = re.search(r'Slide (\d+)', insertion_comment)
    if not slide_num_match:
        print("Error: Could not parse slide number from insertion comment.", file=sys.stderr)
        sys.exit(1)
    first_slide_num = int(slide_num_match.group(1))
    max_slide = count_slides(html)
    current_total = find_total_span(html)

    html = html.replace(
        insertion_comment,
        presenter_html + "\n" + insertion_comment
    )

    for i in range(max_slide, first_slide_num - 1, -1):
        html = re.sub(
            rf'(<div\s[^>]*\bid="s){i}(")',
            rf'\g<1>{i + 1}\2',
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
            f'<span id="total">{new_total}</span>'
        )

    return html


def parse_presenters(args: list[str]) -> tuple[str, list[dict]]:
    """Parse command-line arguments into the deck path and presenter list.

    Args:
        args: Raw sys.argv[1:] arguments.

    Returns:
        A tuple of (deck_path, presenters_list).

    Raises:
        SystemExit: On invalid arguments.
    """
    if not args or args[0].startswith("-"):
        print(
            "Usage: insert_presenter.py <deck.html> "
            "--name NAME --title TITLE [--photo FILE] [...]",
            file=sys.stderr,
        )
        sys.exit(1)

    deck_path = args[0]
    if not Path(deck_path).is_file():
        print(f"Error: Deck file not found: {deck_path}", file=sys.stderr)
        sys.exit(1)

    presenters = []
    current = {}
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--name" and i + 1 < len(args):
            if current.get("name"):
                presenters.append(current)
                current = {}
            current["name"] = args[i + 1]
            i += 2
        elif arg == "--title" and i + 1 < len(args):
            current["title"] = args[i + 1]
            i += 2
        elif arg == "--photo" and i + 1 < len(args):
            current["photo"] = args[i + 1]
            i += 2
        else:
            print(f"Error: Unknown argument: {arg}", file=sys.stderr)
            sys.exit(1)

    if current.get("name"):
        presenters.append(current)

    if not presenters:
        print("Error: At least one --name/--title pair is required.", file=sys.stderr)
        sys.exit(1)

    for p in presenters:
        if "title" not in p:
            print(f"Error: Missing --title for presenter '{p['name']}'", file=sys.stderr)
            sys.exit(1)

    return deck_path, presenters


def main() -> None:
    """Parse arguments, process images, build and insert the presenter slide."""
    deck_path, presenters = parse_presenters(sys.argv[1:])

    for p in presenters:
        if "photo" in p:
            photo_path = os.path.expanduser(p["photo"])
            if not Path(photo_path).is_file():
                print(f"Warning: Photo not found '{photo_path}', using placeholder.", file=sys.stderr)
            else:
                p["b64"] = image_to_base64(photo_path)

    presenter_html = build_presenter_slide(presenters)

    with open(deck_path, encoding="utf-8") as f:
        html = f.read()

    html = insert_slide(html, presenter_html)

    with open(deck_path, "w", encoding="utf-8") as f:
        f.write(html)

    names = ", ".join(p["name"] for p in presenters)
    total_match = re.search(r'<span id="total">(\d+)</span>', html)
    total = total_match.group(1) if total_match else "?"
    print(f"Done — inserted presenter slide ({names}), {total} slides total.")


if __name__ == "__main__":
    main()
