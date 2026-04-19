# Export to PowerPoint

Use `export_to_pptx.py` to convert a finished html-presentation-skill deck into a `.pptx` file. Each slide is captured as a high-resolution screenshot and assembled into a PowerPoint presentation with speaker notes.

## Prerequisites

### `uv` required

This script has heavy dependencies (`playwright`, `python-pptx`, `Pillow`, `beautifulsoup4`). The `run_script.py` wrapper only supports it via the `uv run` path — the fallback shared `.venv` does **not** include these packages. Verify `uv` is available:

```bash
uv --version
```

If `uv` is missing, install it: `pip install uv` or follow https://docs.astral.sh/uv/getting-started/installation/.

### One-time browser setup

Playwright must download a Chromium browser binary before first use. This only needs to happen once per machine:

```bash
uv run python -m playwright install chromium
```

## Command

```bash
python scripts/run_script.py export_to_pptx.py <deck.html> [-o output.pptx]
```

- `<deck.html>` — path to the finished html-presentation-skill HTML file
- `-o output.pptx` — optional output path; defaults to the same folder as the HTML with `.pptx` extension

Example:

```bash
python scripts/run_script.py export_to_pptx.py acme/cortex-ai/cortex-ai-engineering-team-slides.html
# Output: acme/cortex-ai/cortex-ai-engineering-team-slides.pptx
```

## What it produces

| Property | Value |
|---|---|
| Slide size | 13.33 × 7.5 inches (standard widescreen) |
| Screenshot resolution | 3840 × 2160 px (2× device pixel ratio) |
| DPI metadata | 288 DPI (prevents PowerPoint auto-compression) |
| Speaker notes | Copied from `<div class="speaker-notes">` to the notes pane |

## Limitations (communicate to user)

- **Screenshot-based export**: slides are rendered as images — text, shapes, and diagrams are not editable in PowerPoint.
- **Animations not exported**: all animation classes are forced to their final visible state before screenshotting. The exported deck shows the completed state of each slide.
- **Navigation UI hidden**: the slide counter and arrow buttons are hidden during capture.
- **External fonts**: a local HTTP server is started automatically so Google Fonts and other external font URLs load correctly before screenshotting.

## Shell Safety

Never use heredoc syntax or multi-line strings when invoking this script. Always call it as a single-line command through `run_script.py`:

```bash
python scripts/run_script.py export_to_pptx.py <deck.html>
```

## Common Errors

| Error message | Cause | Fix |
|---|---|---|
| `Failed to launch Chromium` | Browser binary not installed | Run `uv run python -m playwright install chromium` |
| `Could not start HTTP server on port 8765` | Port already in use | Kill the process: `lsof -ti :8765 \| xargs kill -9` |
| `No slides found in <file>` | File is not a valid html-presentation-skill deck | Verify the HTML contains `<div id="s1">`, `<div id="s2">`, ... |
| `Could not decode ... as UTF-8` | File has non-UTF-8 encoding | Ensure the HTML was saved with UTF-8 encoding |
| `Could not write output file` | Output path is read-only or open in PowerPoint | Close the file in PowerPoint and retry; check write permissions |
