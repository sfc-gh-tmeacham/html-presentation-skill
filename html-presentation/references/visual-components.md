# Visual Components Reference

Every slide MUST use at least one of these components. Text-only slides are not allowed.

**Required rules (validator-enforced):**
- **External links:** Every `<a href="https://...">` MUST include `target="_blank" rel="noopener"` — the validator fails any external anchor missing either attribute.
- **List alignment:** Every `<ul>` and `<ol>` MUST include `text-align:left` as an inline style or via a CSS class — prevents misalignment when a parent container centers text.
- **Connector arrows and flow lines MUST use `var(--accent)` or a bright visible color — NEVER `var(--border)`, dark gray, or any color that blends into the dark slide background.** This applies to: Material Icon `arrow_forward` between step flow cards, SVG `<line>` and `<path>` connectors in architecture/inline diagrams, and any other visual connector element. Invisible arrows defeat the purpose of a flow diagram.

---

## Card Grid
2–4 cards in a row, each with an icon, title, and one-line description.
Use for: features, benefits, categories.

```html
<div class="card-grid anim stagger">
  <div class="card">
    <span class="material-icons-round" style="color:var(--accent);font-size:32px;">icon_name</span>
    <h4>Title</h4>
    <p>One-line description.</p>
  </div>
</div>
```
```css
.card-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 24px; width: 100%; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 28px 24px; text-align: center; }
```

---

## Comparison Panel
Two columns side by side with a divider.
Use for: old vs new, before vs after, tool A vs tool B.

```html
<div style="display:grid;grid-template-columns:1fr auto 1fr;gap:32px;align-items:start;width:100%;">
  <div class="card"><h4>Option A</h4><ul class="icon-list" style="list-style:none;padding:0;text-align:left;">...</ul></div>
  <div style="width:1px;background:var(--border);align-self:stretch;"></div>
  <div class="card"><h4>Option B</h4><ul class="icon-list" style="list-style:none;padding:0;text-align:left;">...</ul></div>
</div>
```

---

## Stat Callout
One huge number with a short label.
Use for: impressive data points, growth numbers, costs.

```html
<div class="anim" style="text-align:center;">
  <div style="font-size:96px;font-weight:800;color:var(--accent);line-height:1;">42%</div>
  <p style="font-size:22px;color:var(--secondary);margin-top:8px;">Label text</p>
</div>
```

---

## Step Flow
Numbered steps with arrows between them.
Use for: processes, tutorials, how-it-works.

```html
<div style="display:flex;align-items:center;gap:16px;width:100%;">
  <div class="card" style="flex:1;text-align:center;">
    <div style="font-size:32px;font-weight:700;color:var(--accent);">01</div>
    <h4>Step Name</h4>
    <p style="font-size:14px;">Description</p>
  </div>
  <span class="material-icons-round" style="color:var(--accent);font-size:32px;">arrow_forward</span>
  <!-- repeat -->
</div>
```

---

## Quote Block
Large quotation marks, italic text, attribution below.
Use for: testimonials, expert quotes, key statements.

```html
<div class="anim" style="max-width:700px;text-align:center;">
  <div style="font-size:80px;color:var(--accent);line-height:0.5;margin-bottom:16px;">"</div>
  <p style="font-size:26px;font-style:italic;line-height:1.6;">Quote text here.</p>
  <p style="font-size:16px;color:var(--secondary);margin-top:20px;">— Attribution</p>
</div>
```

---

## Icon + Label List
Vertical list with Material Icons on the left, labels on the right.
Use for: feature lists, checklists, requirements.

**Important:** When list items use a leading icon or symbol, the parent `<ul>` MUST set `list-style:none;padding:0;` to suppress browser default bullets.

```html
<ul class="icon-list anim stagger" style="list-style:none;padding:0;text-align:left;">
  <li style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
    <span class="material-icons-round" style="color:var(--accent);">check_circle</span>
    <span>Item label</span>
  </li>
</ul>
```

---

## Code Block
Monospace text on a dark card with syntax-style coloring.
Use for: code examples, command line, config files.

**`white-space: pre-wrap` is required** — without it, all code collapses to a single line.

```css
.code-block {
  background: #111;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px 28px;
  text-align: left;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 16px;
  line-height: 1.7;
  color: #e0e0e0;
  overflow-x: auto;
  width: 100%;
  white-space: pre-wrap; /* REQUIRED — preserves indentation and line breaks */
}
.code-block .kw  { color: var(--accent); font-weight: 600; }
.code-block .str { color: #10B981; }
.code-block .var { color: #F59E0B; }
.code-block .cm  { color: #555; font-style: italic; }
```

Wrap tokens in `<span class="kw">`, `<span class="str">`, `<span class="var">`, `<span class="cm">`.

---

## Timeline
Horizontal line with dots and labels above/below.
Use for: history, roadmap, project phases.

```html
<div style="position:relative;width:100%;padding:40px 0;">
  <div style="position:absolute;top:50%;left:0;right:0;height:2px;background:var(--border);transform:translateY(-50%);"></div>
  <div style="display:flex;justify-content:space-between;position:relative;">
    <div style="text-align:center;">
      <div style="width:14px;height:14px;border-radius:50%;background:var(--accent);margin:0 auto 12px;"></div>
      <p style="font-size:14px;font-weight:600;">Label</p>
      <p style="font-size:12px;color:var(--secondary);">Date or detail</p>
    </div>
  </div>
</div>
```

---

## Image + Caption
Centered image with a caption below.
Use for: screenshots, diagrams, product photos.

```html
<div class="anim" style="text-align:center;">
  <img src="{{IMG:path/to/image.png}}" alt="Description"
    style="max-width:600px;max-height:360px;border-radius:12px;display:block;margin:0 auto;">
  <p style="font-size:15px;color:var(--secondary);margin-top:12px;">Caption text</p>
</div>
```

---

## Metric Dashboard
3–4 stat boxes in a row.
Use for: KPIs, performance data, comparisons.

```html
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px;width:100%;">
  <div class="card anim" style="text-align:center;">
    <div style="font-size:52px;font-weight:800;color:var(--accent);">99%</div>
    <p style="font-size:15px;color:var(--secondary);margin-top:6px;">Metric Label</p>
  </div>
</div>
```

---

## Architecture Diagram
Inline SVG boxes connected by arrows showing system components and data flow.
Use `stroke-dasharray` animation to draw connection lines on slide enter.
Use for: system architecture, data pipelines, integration maps.

Build from basic SVG shapes (`rect`, `circle`, `path`, `text`). Keep it readable at 900px wide.

**Connector lines and arrowheads MUST use `var(--accent)` or a contrasting bright color** — never `stroke="#2a2a2a"`, `stroke="var(--border)"`, or any near-black/dark-gray value. On a dark slide background these are invisible. Use `stroke="var(--accent)"` or a specific bright hex (e.g. `#29B5E8`, `#10B981`) for every `<line>`, `<path>`, and SVG marker stroke.

**SVG container max-height must be ≥ 58vh.** Wrap the SVG in a `<div>` with `style="max-height:65vh;width:100%;"` — values below 58vh create blank bands on the slide and will trigger a validator warning.

**MUST run `svg_calc.py` before writing any SVG coordinates — never hand-write estimates:**

```
# 1. Size every rect to fit its longest label (prevents silent text overflow)
python scripts/run_script.py svg_calc.py textbox --text "Your longest label here" --font-size 11
# → outputs min_rect_w; your <rect width> must be ≥ that value

# 2. Get a tight viewBox height (prevents blank bands at top/bottom)
python scripts/run_script.py svg_calc.py viewbox --content-height <H> --rows <N>
# → outputs exact viewBox height and recommended start-y

# 3. For stacked boxes in a column, get exact y positions AND required container height
python scripts/run_script.py svg_calc.py stack --count <N> --box-height <H> --gap <G> --container-y <container_rect_y>
# → outputs container_height; set your outer <rect height> to that value — NOT the viewBox height
```

Run step 1 for **every text label** in the SVG. A label that looks short at small font sizes can still overflow — the s9 incident had a 303px label in a 230px box at font-size 9.5.

---

## Progress Ring
SVG circle with animated `stroke-dashoffset` fill. Large percentage centered inside.
Use for: scores, completion rates, capacity metrics.

```html
<svg width="180" height="180" viewBox="0 0 180 180">
  <circle cx="90" cy="90" r="80" fill="none" stroke="var(--border)" stroke-width="12"/>
  <circle class="ring-fill" cx="90" cy="90" r="80" fill="none" stroke="var(--accent)"
    stroke-width="12" stroke-linecap="round" transform="rotate(-90 90 90)"
    style="--target-offset:80;"/>
  <text x="90" y="97" text-anchor="middle" fill="white" font-size="36" font-weight="700">75%</text>
</svg>
```

---

## Animated Counter
Large number rolling up from 0 to target using CSS `@property`.
Use for: key stats where animation reinforces magnitude.

See `reference/css-animations.md` pattern 5.

---

## Gradient Illustration
CSS-only decorative visual using radial/linear gradients and layered shapes.
Use for: title slides, section dividers, takeaway slides.

```html
<div style="position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:0;">
  <div style="position:absolute;top:-200px;right:-200px;width:600px;height:600px;
    border-radius:50%;background:radial-gradient(circle,rgba(41,181,232,0.15),transparent 70%);"></div>
</div>
```

---

## Inline SVG Diagram
Custom SVG built from basic shapes depicting a concept. Arrows connect nodes.
Use for: concept maps, relationship diagrams, layered models.

Build entirely with `<svg>` using `rect`, `circle`, `path`, `text`, `line`. No external assets.

**SVG container max-height must be ≥ 58vh** — same rule as Architecture Diagram above.

**MUST run `svg_calc.py` before writing coordinates** — same pre-flight as Architecture Diagram above. At minimum run `textbox` for every label and `viewbox` for the overall height.

---

## Custom Graphic
User-provided image (logo, screenshot, diagram) embedded in the slide.
Use for: branding, product screenshots, partner logos.

Always pair with a caption or heading. See `reference/graphics-embedding.md` for technical requirements.

---

## Table
Styled HTML table for structured data comparisons.
Use for: feature matrices, multi-column comparisons, spec sheets, data grids.

```html
<div class="anim" style="width:100%;overflow-x:auto;">
  <table style="width:100%;border-collapse:collapse;font-size:16px;">
    <thead>
      <tr>
        <th style="padding:12px 16px;text-align:left;border-bottom:2px solid var(--accent);color:var(--accent);font-weight:600;">Column A</th>
        <th style="padding:12px 16px;text-align:left;border-bottom:2px solid var(--accent);color:var(--accent);font-weight:600;">Column B</th>
        <th style="padding:12px 16px;text-align:left;border-bottom:2px solid var(--accent);color:var(--accent);font-weight:600;">Column C</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom:1px solid var(--border);">
        <td style="padding:12px 16px;">Value</td>
        <td style="padding:12px 16px;">Value</td>
        <td style="padding:12px 16px;">Value</td>
      </tr>
      <!-- alternate row shading -->
      <tr style="background:rgba(255,255,255,0.03);border-bottom:1px solid var(--border);">
        <td style="padding:12px 16px;">Value</td>
        <td style="padding:12px 16px;">Value</td>
        <td style="padding:12px 16px;">Value</td>
      </tr>
    </tbody>
  </table>
</div>
```

Accent-color the header row bottom border. Alternate `rgba(255,255,255,0.03)` row shading for readability. Use `<span class="material-icons-round" style="color:#10B981;font-size:18px;">check</span>` / `<span style="color:#EF4444;">✗</span>` for yes/no cells.

---

## Two-Column Layout
General-purpose split slide: content on the left, visual on the right (or vice versa).
Use for: concept + diagram, list + screenshot, text + chart, any "explain and show" pairing.

```html
<div class="anim" style="display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center;width:100%;">
  <div>
    <h2 style="font-size:36px;margin-bottom:16px;">Left Heading</h2>
    <p style="font-size:18px;color:var(--secondary);line-height:1.6;">Supporting text or list goes here.</p>
    <ul class="icon-list" style="list-style:none;padding:0;margin-top:16px;text-align:left;">
      <li style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
        <span class="material-icons-round" style="color:var(--accent);">check_circle</span>
        <span>Key point</span>
      </li>
    </ul>
  </div>
  <div style="display:flex;justify-content:center;align-items:center;">
    <!-- inline SVG, image, diagram, or code block goes here -->
  </div>
</div>
```

Swap column order with `grid-template-columns: 1fr 1fr` and reversing child order when the visual should lead. For asymmetric emphasis use `grid-template-columns: 2fr 3fr` or `3fr 2fr`.

---

## CTA Block
Call-to-action for takeaway and closing slides.
Use for: next steps, sign-ups, links to resources, closing a presentation.

```html
<div class="anim" style="text-align:center;display:flex;flex-direction:column;align-items:center;gap:28px;">
  <h2 style="font-size:52px;font-weight:800;">Ready to get started?</h2>
  <p style="font-size:20px;color:var(--secondary);max-width:560px;line-height:1.6;">Supporting one-liner that reinforces the call to action.</p>
  <a href="https://example.com" target="_blank" rel="noopener"
    style="display:inline-block;padding:16px 40px;background:var(--accent);color:#000;
    font-weight:700;font-size:18px;border-radius:40px;border-bottom:none;
    transition:opacity 0.2s;cursor:pointer;"
    onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'">
    Button Label
  </a>
  <div style="display:flex;gap:32px;flex-wrap:wrap;justify-content:center;margin-top:8px;">
    <a href="https://example.com" target="_blank" rel="noopener"
      style="font-size:15px;color:var(--secondary);border-bottom:1px solid var(--border);">
      Resource Link 1
    </a>
    <a href="https://example.com" target="_blank" rel="noopener"
      style="font-size:15px;color:var(--secondary);border-bottom:1px solid var(--border);">
      Resource Link 2
    </a>
  </div>
</div>
```

The primary button uses a filled pill style with the accent color. Secondary resource links sit below in a muted row. Button text color should contrast with the accent (`#000` for light accents, `#fff` for dark accents).

---

## Callout Banner
Highlighted accent banner for warnings, prerequisites, key notes, or tips.
Use for: important caveats, feature flags, "before you begin" notices, pro tips.

```html
<div class="anim" style="display:flex;align-items:flex-start;gap:16px;
  background:rgba(41,181,232,0.1);border:1px solid rgba(41,181,232,0.35);
  border-left:4px solid var(--accent);border-radius:12px;
  padding:20px 24px;width:100%;max-width:800px;margin:16px auto;">
  <span class="material-icons-round" style="color:var(--accent);font-size:24px;flex-shrink:0;margin-top:2px;">info</span>
  <div>
    <p style="font-weight:600;font-size:16px;margin-bottom:4px;">Banner Title</p>
    <p style="font-size:15px;color:var(--secondary);line-height:1.5;">Supporting detail text for the callout.</p>
  </div>
</div>
```

Swap icon and border color by intent:
- **Info / tip:** `info` icon, accent color
- **Warning:** `warning` icon, `#F59E0B` amber
- **Error / blocker:** `error` icon, `#EF4444` red
- **Success / done:** `check_circle` icon, `#10B981` green

Replace the hardcoded `rgba(41,181,232,...)` tints with the appropriate color at 10% opacity.

---

## Tag / Badge Row
Horizontal row of pill-shaped badges for technologies, categories, or feature labels.
Use for: tech stacks, product feature tags, supported platforms, skill sets.

```html
<div class="anim" style="display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-top:16px;">
  <span style="display:inline-flex;align-items:center;gap:6px;
    padding:8px 18px;border-radius:999px;
    background:rgba(41,181,232,0.12);border:1px solid rgba(41,181,232,0.3);
    font-size:15px;font-weight:500;color:var(--accent);">
    <span class="material-icons-round" style="font-size:16px;">code</span>
    Python
  </span>
  <span style="display:inline-flex;align-items:center;gap:6px;
    padding:8px 18px;border-radius:999px;
    background:rgba(255,255,255,0.06);border:1px solid var(--border);
    font-size:15px;font-weight:500;color:var(--text);">
    SQL
  </span>
  <!-- repeat for each tag -->
</div>
```

Use the accent-tinted style for primary/highlighted tags and the neutral `rgba(255,255,255,0.06)` style for secondary tags. Optionally include a leading Material Icon inside the badge for visual variety.

---

## Presenter Slide

Use for the optional presenter slide immediately after the Title slide. See SKILL.md for layout rules by presenter count (1 = centered, 2 = side-by-side, 3+ = card grid).

**Single presenter:**
```html
<h3 class="anim">Presented By</h3>
<div class="anim" style="display:flex;flex-direction:column;align-items:center;gap:16px;transition-delay:0.1s;">
  <img src="data:image/png;base64,..." alt="Presenter Name"
    style="width:clamp(100px,12vmin,160px);height:clamp(100px,12vmin,160px);border-radius:50%;object-fit:cover;border:3px solid var(--accent);">
  <div style="text-align:center;">
    <h4 style="font-size:clamp(1.5rem,2.5vw,2.25rem);margin-bottom:0.25rem;">Presenter Name</h4>
    <p style="font-size:clamp(1rem,1.5vw,1.5rem);color:var(--secondary);">Title / Role</p>
  </div>
</div>
```

**Multiple presenters (2-column shown; adjust `repeat(N,1fr)` for 3+):**
```html
<h3 class="anim">Your Presenters</h3>
<div class="card-grid anim stagger" style="grid-template-columns:repeat(2,1fr);gap:24px;transition-delay:0.1s;">
  <div class="card" style="text-align:center;padding:28px 24px;">
    <img src="data:image/png;base64,..." alt="Name"
      style="width:clamp(80px,10vmin,140px);height:clamp(80px,10vmin,140px);border-radius:50%;object-fit:cover;border:3px solid var(--accent);margin-bottom:0.75rem;">
    <h4 style="font-size:clamp(1.1rem,2vw,1.5rem);margin-bottom:0.25rem;">Presenter Name</h4>
    <p style="font-size:clamp(0.875rem,1.3vw,1.125rem);color:var(--secondary);">Title / Role</p>
  </div>
  <!-- repeat for each presenter -->
</div>
```

---

## Title Slide

Use for the opening slide of any deck. Features an animated gradient background, ambient glow orbs, the Snowflake logo, and a center-stacked heading group.

**Required CSS** — add to the deck's `<style>` block:

```css
@keyframes gradientShift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
.gradient-bg {
  background: linear-gradient(135deg, #0a0a0a, #0d1f2d, #0a0a0a, #0d1a10);
  background-size: 400% 400%;
  animation: gradientShift 12s ease infinite;
}
```

**Apply to the slide div:**

```html
<div id="s1" class="slide gradient-bg active">
```

**Full title slide body:**

```html
<div id="s1" class="slide gradient-bg active">
  <!-- Ambient glow orbs -->
  <div style="position:absolute;inset:0;overflow:hidden;pointer-events:none;">
    <div style="position:absolute;top:-180px;right:-180px;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(41,181,232,0.12),transparent 70%);"></div>
    <div style="position:absolute;bottom:-150px;left:-150px;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(41,181,232,0.08),transparent 70%);"></div>
  </div>
  <div class="slide-inner" style="text-align:center;">
    <!-- Snowflake logo -->
    <div class="anim" style="margin-bottom:0.5rem;">
      <svg viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" aria-label="Snowflake" role="img"
        style="display:block;margin:0 auto clamp(10px,2vh,18px);height:clamp(44px,7vh,80px);width:auto;">
        <!-- paste Snowflake SVG paths here -->
      </svg>
    </div>
    <!-- Category / industry label -->
    <h3 class="anim" style="transition-delay:0.1s;">Category or Industry Name</h3>
    <!-- Main title — gradient text -->
    <h2 class="anim" style="transition-delay:0.2s;font-size:clamp(2.8rem,5vw,5rem);background:linear-gradient(135deg,#ffffff 40%,#29B5E8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
      Presentation Title
    </h2>
    <!-- Subtitle -->
    <p class="anim" style="transition-delay:0.3s;font-size:clamp(1.3rem,2.2vw,2rem);color:var(--secondary);">Subtitle or Pillar Name</p>
    <!-- Accent divider -->
    <div class="anim" style="transition-delay:0.4s;width:60px;height:3px;background:var(--accent);border-radius:2px;margin:0.25rem auto;"></div>
    <!-- Tagline / descriptor -->
    <p class="anim" style="transition-delay:0.5s;font-size:clamp(0.85rem,1.2vw,1rem);color:#555;margin-top:0.25rem;">Key theme · Key theme · Key theme</p>
  </div>
  <div class="speaker-notes">Speaker notes here.</div>
</div>
```

**Key style decisions:**
- `gradient-bg` class drives the slow animated background — add the CSS above to every deck that uses this layout
- Gradient text on `h2` uses `background:linear-gradient(135deg,#ffffff 40%,#29B5E8)` with `-webkit-background-clip:text` — white bleeds into Snowflake blue
- Glow orbs use `position:absolute` with `pointer-events:none` so they don't block clicks; place them inside the slide div before `.slide-inner`
- Accent divider is 60 × 3px — use it between the subtitle and tagline to add visual rhythm
- All children use `class="anim"` with staggered `transition-delay` for entrance animation
