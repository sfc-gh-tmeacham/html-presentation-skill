# HTML Presentation

A [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) skill that generates beautiful, self-contained HTML slide decks from a natural language conversation.

## Why HTML?

- **Zero dependencies** — every deck is a single `.html` file. No PowerPoint, no Google account, no internet connection needed to present.
- **Pixel-perfect on any device** — open it in any browser, on any OS, and it looks exactly the same.
- **Version-control friendly** — it's just text. Diff it, commit it, review it.
- **Fully customizable** — every pixel is CSS you can tweak after generation.

## What You Get

- Dark-themed, widescreen slides with smooth crossfade transitions
- Rich visual components: card grids, stat callouts, step flows, comparison panels, metric dashboards, architecture diagrams, progress rings, animated counters, and more
- Presenter slide with circular-cropped headshot photos
- Agenda slide with icon cards
- Speaker notes in a separate popup window (press `N`)
- Keyboard navigation (arrow keys) with a slide counter
- CSS animations that respect `prefers-reduced-motion`
- Google Material Icons throughout
- User-provided images (logos, screenshots, headshots) embedded as base64 — no external files
- QR code appendix slide with scannable codes for every external link in the deck

## How to Use

In Cortex Code, just ask:

```
make an html presentation about [your topic]
```

The skill walks you through a guided conversation:

1. **Gather** — topic, audience, slide count, accent color, speaker notes, images, presenter info
2. **Plan** — a slide-by-slide outline with visual components mapped to each slide
3. **Build** — generates the HTML file
4. **Preview** — opens in your default browser
5. **Verify** — runs an automated validator (`validate_deck.py`)
6. **Iterate** — refine wording, add/remove slides, swap visuals until you're happy

## Helper Scripts

The `scripts/` directory contains Python utilities that handle image processing, embedding, and validation. All scripts run inside an isolated virtual environment managed by `run_script.py` — no global installs required.

| Script | Purpose |
|--------|---------|
| `run_script.py` | Wrapper — creates/reuses a venv and runs any script below |
| `resize_image.py` | Resize raster images (Lanczos downscale) |
| `img_to_base64.py` | Convert any image to a base64 data URI |
| `screenshot_to_slide.py` | Auto-crop whitespace + resize + base64 in one step |
| `svg_optimize.py` | Strip SVG editor metadata for smaller output |
| `color_swap_svg.py` | Recolor SVG fills/strokes for dark backgrounds |
| `embed_image.py` | Replace `{{IMG:...}}` placeholders in HTML with base64 data URIs |
| `insert_presenter.py` | Inject a presenter slide (resize + base64 + insert + renumber) |
| `validate_deck.py` | Lint a finished deck for common issues |
| `generate_qr_appendix.py` | Append a QR code "Resources" slide for all external links |

## Example Output

A typical 9-slide deck on "Snowflake Cortex AI" produces a single ~120 KB HTML file with:

- Title slide with gradient background
- Presenter slide with circular headshot
- Agenda with 5-section icon card grid
- Stat callout (73% of enterprises struggle with AI infra)
- 3-pillar card grid (LLM Functions, ML Functions, AI Services)
- Step flow diagram (Data → Cortex → Insights → Production)
- Side-by-side comparison panel (Traditional vs Cortex)
- 4-metric dashboard
- Call-to-action with action chips

## File Structure

```
html-presentation/
├── README.md          ← you are here
├── SKILL.md           ← LLM-facing skill definition (workflow, rules, patterns)
└── scripts/
    ├── run_script.py
    ├── resize_image.py
    ├── img_to_base64.py
    ├── screenshot_to_slide.py
    ├── svg_optimize.py
    ├── color_swap_svg.py
    ├── embed_image.py
    ├── insert_presenter.py
    ├── validate_deck.py
    └── generate_qr_appendix.py
```
