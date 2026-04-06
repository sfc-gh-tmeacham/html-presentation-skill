# Graphics Embedding Rules

All custom graphics MUST be embedded inline to keep the HTML fully self-contained with zero external dependencies. Use the correct placeholder token for each asset type — the embed phase resolves all tokens automatically.

## Environment

NEVER run helper scripts in the global Python environment. Always use the `scripts/run_script.py` wrapper, which automatically creates and reuses an isolated virtual environment (preferring `uv` if available, falling back to `python -m venv`). Works on macOS, Linux, and Windows. The venv and its dependencies (Pillow, segno) are installed on first run and cached in `scripts/.venv/`.

```bash
python scripts/run_script.py <script.py> [args...]
```

## Shell Safety

**Never use heredoc syntax or multi-line `python3 -c "..."` strings in bash** — the shell gets stuck waiting for the terminator and the session hangs. This applies to all script invocations in this skill.

When you need to run Python logic that doesn't fit in a single argument:
1. Use the `write` tool to save a `.py` file to `/tmp/`
2. Run it with `python3 /tmp/script.py`

For all asset embedding operations, use `scripts/run_script.py <script.py> [args]` — every call is a single line.

## Available Scripts

| Script | Purpose |
|---|---|
| `run_script.py <script.py> [args...]` | **Wrapper** — creates/reuses uv venv and runs any script below |
| `img_to_base64.py <file>` | Convert any image (raster or SVG) to a base64 data URI |
| `resize_image.py <in> <out> [--max-size 800]` | Resize raster image, Lanczos downscale |
| `screenshot_to_slide.py <in> [--max-size] [--padding]` | Auto-crop + resize + base64 in one step |
| `svg_optimize.py <in> [out]` | Strip SVG metadata/comments for smaller output |
| `color_swap_svg.py <in> [out] [--from-color] [--to-color]` | Recolor SVG fills/strokes for dark backgrounds |
| `embed_image.py <deck.html> [--max-size 800] [--dry-run]` | Resolve all `{{IMG:...}}`, `{{SNOWFLAKE_LOGO}}`, and `{{SVG_INLINE:...}}` tokens |
| `insert_presenter.py <deck.html> --name N --title T [--photo F]` | Insert presenter slide (resize + base64 + inject + renumber) |
| `validate_deck.py <deck.html>` | Lint a finished deck: IDs, counter, placeholders, accessibility, transitions |
| `validate_urls.py <file>` | Check every external URL in a brief (`.md`) or deck (`.html`) returns HTTP 200 |
| `generate_qr_appendix.py <deck.html>` | Scan for external links, append QR code "Resources" slide |

## Placeholder Tokens — Which to Use

Three tokens are available. **Always prefer the one highest in this table** for the asset type:

| Token | Asset type | Result | When to use |
|---|---|---|---|
| `{{SNOWFLAKE_LOGO}}` | Snowflake logo only | Inline `<svg>` | Title slide logo — always use this, never `{{IMG:...}}` or `{{SVG_INLINE:...}}` for the Snowflake logo |
| `{{SVG_INLINE:path}}` | User-provided `.svg` | Inline `<svg>` | Customer logos, icon graphics, diagrams supplied as SVG files — **preferred over `{{IMG:...}}` for all SVGs** |
| `{{IMG:path}}` | Raster images (PNG/JPG/GIF/WebP) and SVGs you need inside an `<img>` tag | `data:` URI | Photos, screenshots, raster graphics; also use for SVGs that must live in an `<img>` element |

**Why `{{SVG_INLINE:...}}` beats `{{IMG:...}}` for SVGs:**
- No base64 overhead (SVGs are already text)
- Inline SVGs can inherit `var(--accent)` and other CSS custom properties
- Directly styleable/animatable with CSS
- No `<img>` wrapper needed — places cleanly as a block element

## Raster Images (PNG, JPG, GIF, WebP)

1. Resize if needed: `scripts/run_script.py resize_image.py <input> <output> --max-size 800`
2. Use `{{IMG:path}}` placeholder in the HTML: `<img src="{{IMG:path/to/image.png}}" alt="description">`
3. Use `object-fit: contain` so the image is never stretched or cropped.

## Screenshots and Photos

Use `scripts/run_script.py screenshot_to_slide.py <input> [--max-size 800] [--padding 0]` to auto-crop whitespace, resize, and get a base64 URI in one step. Add `--padding 16` for breathing room.

## SVG Graphics

### User-provided SVG (logos, icons, diagrams)

Use `{{SVG_INLINE:path}}` as a standalone token where the SVG should appear:

```html
{{SVG_INLINE:customer-logo.svg}}
```

Pass an optional CSS style string (second arg, separated by `|`) to control sizing and positioning:

```html
{{SVG_INLINE:customer-logo.svg|height:60px;display:block;margin:0 auto}}
```

The style is injected onto the root `<svg>` element. User-provided SVGs are automatically sanitized: `<script>` elements, `on*` event handlers, `javascript:` URIs, XML declarations, and HTML comments are stripped before injection.

**Pre-processing SVGs before use:**
1. Optimize: `scripts/run_script.py svg_optimize.py <input.svg> <output.svg>`
2. Recolor if needed (dark fills on dark bg): `scripts/run_script.py color_swap_svg.py <in> <out> --from-color "#000" --to-color "#fff"`
3. Then reference with `{{SVG_INLINE:path}}` — no manual `<path>` copying required.

### Snowflake Logo

Always use the dedicated `{{SNOWFLAKE_LOGO}}` token. Never use `{{IMG:...}}` or `{{SVG_INLINE:...}}` for the Snowflake logo.

## Context Window Safety (CRITICAL)

- NEVER read base64 data into context. When reading an HTML file with embedded images, use targeted line-range reads or grep to skip over `<img src="data:` lines.
- NEVER paste or type base64 strings into HTML. Use `{{IMG:path}}` placeholders — let `embed_image.py` handle injection.
- NEVER copy SVG `<path>` data manually into HTML. Use `{{SVG_INLINE:path}}` or `{{SNOWFLAKE_LOGO}}` — let `embed_image.py` handle injection.
- NEVER capture stdout of `img_to_base64.py` into context. Use `embed_image.py` which writes directly to the HTML file.
- Paths in all tokens support tilde expansion (`~/Downloads/logo.svg`) and relative paths.
- For presenter headshots, `insert_presenter.py` handles the full pipeline end-to-end.

## CSS Styling for Embedded Graphics

- Rounded corners: `border-radius: 12px`
- Constrain size: `max-width: 400px; max-height: 300px` (never exceed 60% of slide width)
- Center: `display: block; margin: 0 auto`
- Logos: keep small (`max-height: 80px`), position in slide header/footer, not as main visual
- For images that may blend into the dark background: `background: rgba(255,255,255,0.05); padding: 16px; border-radius: 16px`
- Never upscale a small image — display at native size

## User Guidance (communicate during Step 1)

- Transparent backgrounds (PNG/SVG) work best against the dark slide theme
- Vector formats (SVG) are preferred for logos and diagrams — stay sharp at any size
- Large photos or screenshots will be resized automatically
