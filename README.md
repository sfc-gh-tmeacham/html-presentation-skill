# Cortex Code CLI HTML Presentation Skill

[![Built with Cortex Code](https://img.shields.io/badge/Built%20with-Cortex%20Code-29B5E8?style=flat&logo=snowflake&logoColor=white)](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=flat&logo=snowflake&logoColor=white)](https://www.snowflake.com)

A skill for [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) (also compatible with **Project SnowWork — Research Preview**) that generates beautiful, self-contained HTML slide decks from a natural language conversation.

## How to Install This Skill

### Option 1 — Natural language (easiest)

Just paste this into a Cortex Code CLI chat:

```
I want to import this skill as a user skill from github https://github.com/sfc-gh-tmeacham/html-presentation-skill.git
```

Cortex Code will handle the rest automatically.

### Option 2 — CLI command

Inside a Cortex Code CLI or SnowWork session, run:

```
/skill add https://github.com/sfc-gh-tmeacham/html-presentation-skill.git
```

That's it. Cortex Code clones the repo and makes the skill available immediately. To verify it loaded:


```
/skill list
```

You should see `html-presentation` in the list. To use it, just ask to make a presentation — the skill activates automatically. You can also invoke it explicitly:

```
$html-presentation make a deck about Snowflake Cortex AI
```

To update the skill to the latest version:

```
/skill sync html-presentation
```

> For full documentation on Cortex Code skills see [Cortex Code CLI extensibility](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility#label-extensibility-skills).

## Why HTML?

- **Minimal dependencies** — every deck is a single `.html` file with one external dependency: Google Material Icons (loaded from `fonts.googleapis.com`). An internet connection is required to display icons when presenting.
- **Pixel-perfect on any device** — open it in any browser, on any OS, and it looks exactly the same.
- **Version-control friendly** — it's just text. Diff it, commit it, review it.
- **Fully customizable** — every pixel is CSS you can tweak after generation.

## What You Get

- Dark-themed, widescreen slides with smooth crossfade transitions
- Rich visual components: card grids, stat callouts, step flows, comparison panels, metric dashboards, architecture diagrams, progress rings, animated counters, and more
- Presenter slide with circular-cropped headshot photos (up to 9 presenters)
- Agenda slide with icon cards
- Speaker notes in a separate popup window (press `N`)
- Keyboard navigation (arrow keys) with a slide counter
- CSS animations that respect `prefers-reduced-motion`
- Google Material Icons throughout
- User-provided images (logos, screenshots, headshots) embedded as base64 — no external files
- QR code appendix slide with scannable codes for every external link in the deck

## Requirements

- **Python 3.9+** — required by all helper scripts
- **Pillow** — optional; needed for `--max-size` image resizing (`pip install Pillow`)

## How to Use

In Cortex Code CLI or SnowWork, just ask:

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
| `insert_presenter.py` | Inject a presenter slide (resize + base64 + insert + renumber); max 9 presenters |
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
html-presentaion-skill/          ← repo root
├── README.md                    ← you are here
├── .gitignore
└── html-presentation/           ← skill package
    ├── SKILL.md                 ← LLM-facing skill definition (workflow, rules, patterns)
    ├── assets/
    │   └── snowflake-logo.svg
    ├── references/
    │   ├── accent-colors.md
    │   ├── css-animations.md
    │   ├── graphics-embedding.md
    │   └── visual-components.md
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

---

## Disclaimer

> **This skill is not an official offering of Snowflake and is not supported by Snowflake in any way.** It is a community-built tool provided as-is for use with [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) and Project SnowWork (Research Preview).

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
