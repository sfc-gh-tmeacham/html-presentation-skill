#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["urllib3"]
# ///
"""Download the Material Symbols Rounded codepoints file and save icon names.

Fetches the official codepoints file from the Google Material Design Icons
GitHub repository and writes a plain-text list of valid icon names to
``scripts/material_symbols_names.txt`` (one name per line, sorted).

``validate_deck.py`` reads this file to perform exhaustive icon name
validation — catching typos and invented names, not just a known blocklist.

Usage::

    python run_script.py update_icon_list.py

Re-run whenever you want to pick up newly added Material Symbols icons.

Exit codes:

- 0: success
- 1: error — see stderr for details
"""

import sys
import urllib.request
from pathlib import Path

CODEPOINTS_URL = (
    "https://raw.githubusercontent.com/google/material-design-icons/master/"
    "variablefont/MaterialSymbolsRounded%5BFILL%2CGRAD%2Copsz%2Cwght%5D.codepoints"
)

OUTPUT_FILE = Path(__file__).parent / "material_symbols_names.txt"


def main() -> int:
    print(f"Downloading codepoints from GitHub...")
    try:
        with urllib.request.urlopen(CODEPOINTS_URL, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        print(f"ERROR: could not fetch codepoints: {e}", file=sys.stderr)
        return 1

    names = sorted(
        line.split()[0]
        for line in raw.splitlines()
        if line.strip() and not line.startswith("#")
    )

    if not names:
        print("ERROR: parsed 0 icon names — unexpected file format", file=sys.stderr)
        return 1

    OUTPUT_FILE.write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"SUCCESS: {len(names)} icon names written to {OUTPUT_FILE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
