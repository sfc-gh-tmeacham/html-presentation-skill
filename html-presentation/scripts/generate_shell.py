#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""
generate_shell.py — generate the HTML shell for a presentation deck.

Reads templates/shell_template.html, substitutes the three dynamic values
(title, accent color, slide count), optionally strips speaker-notes sections,
then writes the output file with INSERT_SLIDE_1 ready for Phase 2 insertion.

Usage (via run_script.py from html-presentation/):
  python scripts/run_script.py generate_shell.py \\
      --title "My Deck Title" \\
      --accent "#29B5E8" \\
      --slides 18 \\
      --output my-deck/my-deck-all-technical-slides.html \\
      [--no-notes]

Exit codes:
  0  success — file written and all 4 shell checks passed
  1  error — missing args, template not found, or a check failed
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "shell_template.html"

# Matches all three comment styles used for conditional sections in the template:
#   CSS blocks:  /* BEGIN_NAME */ ... /* END_NAME */
#   JS blocks:   // BEGIN_NAME ... // END_NAME
#   HTML blocks: <!-- BEGIN_NAME --> ... <!-- END_NAME -->
SECTION_RE = re.compile(
    r"/\*\s*BEGIN_(?P<name>\w+)\s*\*/.*?/\*\s*END_(?P=name)\s*\*/|"
    r"//\s*BEGIN_(?P<jname>\w+).*?//\s*END_(?P=jname)[^\n]*|"
    r"<!--\s*BEGIN_(?P<hname>\w+)\s*-->.*?<!--\s*END_(?P=hname)\s*-->",
    re.DOTALL,
)

# Section names that belong to the speaker-notes system. All five are stripped
# when --no-notes is passed; all five are kept (markers only removed) otherwise.
NOTES_SECTIONS = {"NOTES_CSS", "NOTES_HTML", "NOTES_JS", "SHOW_UPDATES", "NOTES_KEYS"}

# Valid hex color: optional #, then 3 or 6 hex digits.
HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")


def _fail(message: str, hint: str = "") -> int:
    """Print a structured ERROR block to stderr and return exit code 1.

    The ERROR/HINT format is designed for agent consumption: ERROR states what
    went wrong; HINT states the corrective action to take before retrying.

    Args:
        message: Short description of what failed.
        hint: Actionable instruction telling the agent how to fix the problem.

    Returns:
        Always 1, so callers can write ``return _fail(...)``.
    """
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(f"HINT:  {hint}", file=sys.stderr)
    return 1


def strip_section_markers(html: str, keep_notes: bool) -> str:
    """Remove BEGIN/END section markers from the template, keeping or dropping content.

    Iterates over every marked section in the template. For notes sections,
    the inner content is either preserved (keep_notes=True) or discarded
    (keep_notes=False). All other sections are always kept — only their
    markers are removed.

    Args:
        html: Raw template string containing BEGIN_*/END_* markers.
        keep_notes: When True, speaker-notes section content is kept.
            When False, it is removed entirely from the output.

    Returns:
        Template string with all markers stripped and conditional sections
        resolved.
    """
    def replacer(m: re.Match) -> str:
        name = m.group("name") or m.group("jname") or m.group("hname")
        content_match = re.search(
            r"(?:BEGIN_\w+\s*\*/|BEGIN_\w+[^\n]*\n|BEGIN_\w+\s*-->)(.*?)(?:/\*\s*END|//\s*END|<!--\s*END)",
            m.group(0),
            re.DOTALL,
        )
        inner = content_match.group(1) if content_match else ""
        if name in NOTES_SECTIONS:
            return inner if keep_notes else ""
        return inner

    return SECTION_RE.sub(replacer, html)


def validate_shell(html: str, slide_count: int, accent: str) -> list[tuple[str, str]]:
    """Run the four required shell checks against the rendered HTML string.

    Checks:
        1. INSERT_SLIDE_1 marker exists (Phase 2 edit tool depends on it).
        2. <span id="total"> is present and equals slide_count.
        3. <div class="counter"> exists (required by generate_qr_appendix.py).
        4. The accent hex value appears in the output (confirms substitution ran).

    Args:
        html: Fully rendered HTML string ready to be written to disk.
        slide_count: Expected total slide count from the approved plan.
        accent: Accent hex color string, e.g. "#29B5E8".

    Returns:
        List of (message, hint) tuples for every failed check. Empty list
        means all checks passed.
    """
    failures: list[tuple[str, str]] = []

    if "<!-- INSERT_SLIDE_1 -->" not in html:
        failures.append((
            "INSERT_SLIDE_1 marker is missing from the rendered output",
            "This is a template corruption issue — verify templates/shell_template.html "
            "contains '<!-- INSERT_SLIDE_1 -->' inside <div id='deck'>.",
        ))

    total_match = re.search(r'<span\s+id="total"[^>]*>\s*(\d+)\s*</span>', html, re.IGNORECASE)
    if not total_match:
        failures.append((
            "<span id='total'> element is missing from the rendered output",
            "This is a template corruption issue — verify templates/shell_template.html "
            "contains <span id='total'>{{SLIDE_COUNT}}</span> in the nav block.",
        ))
    elif int(total_match.group(1)) != slide_count:
        found = total_match.group(1)
        failures.append((
            f"<span id='total'> contains {found} but --slides was {slide_count}",
            f"Re-run with --slides {found} to match what the template rendered, "
            f"or check that {{{{SLIDE_COUNT}}}} placeholder is present in the template.",
        ))

    if '<div class="counter">' not in html:
        failures.append((
            "<div class='counter'> marker is missing — generate_qr_appendix.py requires it",
            "This is a template corruption issue — verify templates/shell_template.html "
            "contains <div class='counter'></div> immediately before <div id='nav'>.",
        ))

    if accent.lower() not in html.lower():
        failures.append((
            f"Accent color '{accent}' was not found anywhere in the rendered output",
            f"Check that {{{{ACCENT}}}} placeholder exists in the template :root block "
            f"and that --accent was passed as a full hex value such as '#29B5E8'.",
        ))

    return failures


def main() -> int:
    """Parse arguments, render the shell template, validate, and write output.

    Returns:
        0 on success, 1 on any error.
    """
    parser = argparse.ArgumentParser(description="Generate HTML presentation shell.")
    parser.add_argument("--title", required=True, help="Deck title (used in <title> tag)")
    parser.add_argument("--accent", required=True, help="Accent hex color, e.g. #29B5E8")
    parser.add_argument("--slides", required=True, type=int, help="Total slide count")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--no-notes", dest="notes", action="store_false",
                        help="Omit speaker notes CSS, HTML, and JS")
    parser.set_defaults(notes=True)
    args = parser.parse_args()

    # --- Argument validation -------------------------------------------------

    if not args.title.strip():
        return _fail(
            "--title is empty",
            "Pass a non-empty deck title, e.g. --title \"Cortex AI Overview\".",
        )

    if not HEX_COLOR_RE.match(args.accent.lstrip("#")):
        return _fail(
            f"--accent '{args.accent}' is not a valid hex color",
            "Use a 3- or 6-digit hex value with an optional leading #, "
            "e.g. --accent '#29B5E8'. Check references/accent-colors.md for valid options.",
        )
    # Normalise: ensure the accent value always starts with #
    if not args.accent.startswith("#"):
        args.accent = f"#{args.accent}"

    if args.slides < 1:
        return _fail(
            f"--slides {args.slides} is invalid; slide count must be at least 1",
            "Set --slides to the total number of slides from the approved plan.",
        )

    # --- Template loading ----------------------------------------------------

    if not TEMPLATE_PATH.exists():
        return _fail(
            f"Shell template not found at {TEMPLATE_PATH}",
            "Confirm the script is being run from the html-presentation/ skill root "
            "via run_script.py and that templates/shell_template.html exists.",
        )

    try:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return _fail(
            f"Could not read template at {TEMPLATE_PATH}: {exc}",
            "Check file permissions on templates/shell_template.html.",
        )

    if not template.strip():
        return _fail(
            f"Template file at {TEMPLATE_PATH} is empty",
            "Restore templates/shell_template.html from the git repository.",
        )

    # --- Rendering -----------------------------------------------------------

    html = strip_section_markers(template, keep_notes=args.notes)

    # Warn if any placeholders were not substituted (catches template drift).
    unreplaced = re.findall(r"\{\{[A-Z_]+\}\}", html)
    # Perform the three substitutions.
    html = (html
        .replace("{{TITLE}}", args.title)
        .replace("{{ACCENT}}", args.accent)
        .replace("{{SLIDE_COUNT}}", str(args.slides)))
    # Re-check after substitution.
    still_unreplaced = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if still_unreplaced:
        return _fail(
            f"Template contains unresolved placeholders after substitution: "
            f"{', '.join(still_unreplaced)}",
            "Update templates/shell_template.html to use only the supported "
            "placeholders: {{TITLE}}, {{ACCENT}}, {{SLIDE_COUNT}}.",
        )

    # --- Validation ----------------------------------------------------------

    check_failures = validate_shell(html, args.slides, args.accent)
    if check_failures:
        print(
            f"ERROR: Shell validation failed ({len(check_failures)} check(s)):",
            file=sys.stderr,
        )
        for i, (msg, hint) in enumerate(check_failures, 1):
            print(f"  [{i}] {msg}", file=sys.stderr)
            print(f"       FIX: {hint}", file=sys.stderr)
        print(
            "ACTION: Do not proceed to Phase 2. Fix the issues above and re-run "
            "generate_shell.py with the same arguments.",
            file=sys.stderr,
        )
        return 1

    # --- Write output --------------------------------------------------------

    output = Path(args.output)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
    except OSError as exc:
        return _fail(
            f"Could not write output file '{output}': {exc}",
            f"Check that the directory '{output.parent}' is writable and that "
            "the path argument does not contain invalid characters.",
        )

    # --- Success report ------------------------------------------------------

    notes_status = "speaker notes ON" if args.notes else "speaker notes OFF (--no-notes)"
    print(
        f"SUCCESS: Shell written to {output} | "
        f"slides={args.slides} | accent={args.accent} | {notes_status}"
    )
    print(
        f"NEXT: Proceed to Phase 2. Use the edit tool to replace "
        f"'<!-- INSERT_SLIDE_1 -->' in {output} with the first slide div, "
        f"then append '<!-- INSERT_SLIDE_2 -->' (repeat for each slide)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
