# Visual Components Reference

Every slide MUST use at least one of these components. Text-only slides are not allowed.

**Required rules (validator-enforced):**
- **External links:** Every `<a href="https://...">` MUST include `target="_blank" rel="noopener"` — the validator fails any external anchor missing either attribute.
- **List alignment:** Every `<ul>` and `<ol>` MUST include `text-align:left` as an inline style or via a CSS class — prevents misalignment when a parent container centers text.
- **Connector arrows and flow lines MUST use `var(--accent)` or a bright visible color — NEVER `var(--border)`, dark gray, or any color that blends into the dark slide background.** This applies to: Material Icon `arrow_forward` between step flow cards, SVG `<line>` and `<path>` connectors in architecture/inline diagrams, and any other visual connector element. Invisible arrows defeat the purpose of a flow diagram.
- **Material Icons** — for blacklisted names and a full curated icon list organized by concept and industry, see [`references/material-icons.md`](material-icons.md). Do not invent icon names.

---

## Quick Reference

| Component | Use For | Type |
|---|---|---|
| [Card Grid](#card-grid) | 2–4 cards in a row, icon + title + description | CSS |
| [Comparison Panel](#comparison-panel) | Two columns side by side with a divider | CSS |
| [Stat Callout](#stat-callout) | One huge number with a short label | CSS |
| [Step Flow](#step-flow) | Numbered steps with arrows between them | CSS |
| [Quote Block](#quote-block) | Card with serif opening quote mark, italic text, attribution | CSS |
| [Icon + Label List](#icon--label-list) | Vertical list with icons on left, labels on right | CSS |
| [Code Block](#code-block) | Monospace text on a dark card, syntax coloring | CSS |
| [Timeline](#timeline) | Horizontal line with dots and labels above/below | CSS |
| [Image + Caption](#image--caption) | Centered image with caption below | HTML |
| [Metric Dashboard](#metric-dashboard) | 3–4 stat boxes in a row | CSS |
| [Architecture Diagram](#architecture-diagram) | SVG boxes + arrows for system/data flow | SVG |
| [Progress Ring](#progress-ring) | Animated SVG circle fill with percentage inside | SVG |
| [Animated Counter](#animated-counter) | Large number counting up from 0 to target | CSS |
| [Gradient Illustration](#gradient-illustration) | Decorative CSS gradients / layered shapes | CSS |
| [Inline SVG Diagram](#inline-svg-diagram) | Custom SVG shapes + arrows depicting a concept | SVG |
| [Custom Graphic](#custom-graphic) | User-provided image (logo, screenshot, diagram) | HTML |
| [Table](#table) | Styled HTML table for structured comparisons | HTML |
| [Two-Column Layout](#two-column-layout) | Content left, visual right (or vice versa) | CSS |
| [CTA Block](#cta-block) | Call-to-action for takeaway or closing slides | CSS |
| [Callout Banner](#callout-banner) | Accent banner for warnings, tips, key notes | CSS |
| [Tag / Badge Row](#tag--badge-row) | Pill badges for technologies or categories | CSS |
| [Presenter Slide](#presenter-slide) | Presenter photo, name, title after title slide | CSS |
| [Vertical Bar Chart](#vertical-bar-chart) | Vertical CSS flexbox bars sized by percentage | CSS |
| [Horizontal Bar Chart](#horizontal-bar-chart) | Horizontal CSS bars; best for long labels or 5+ categories | CSS |
| [Line / Area Chart](#line--area-chart) | SVG polyline/polygon for trends over time | SVG |
| [Donut Chart](#donut-chart) | SVG stroke-dasharray segments for part-to-whole | SVG |
| [Title Slide](#title-slide) | Animated gradient opening slide with Snowflake logo | CSS |

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
Card container with an absolutely-positioned serif opening quote mark (`&ldquo;`) in the upper-left corner, italic quote text below with top margin to clear the mark, and an attribution line.
Use for: testimonials, expert quotes, key statements.

**Required `<head>` dependency** — add this line alongside the Material Icons link:
```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
```
This loads Playfair Display 700, used by the opening quote mark. Without it the mark falls back to Georgia/serif but loses the distinctive curly ornate rendering.

```html
<div class="card anim" style="padding:clamp(14px,2vh,22px) clamp(16px,2vw,24px) clamp(14px,2vh,22px);position:relative;">
  <div aria-hidden="true" style="position:absolute;top:-2px;left:10px;font-size:clamp(3.5rem,5.5vw,5rem);color:var(--accent);opacity:0.65;font-family:'Playfair Display',Georgia,'Times New Roman',serif;line-height:1;pointer-events:none;user-select:none;">&ldquo;</div>
  <p style="font-style:italic;font-size:clamp(0.88rem,1.25vw,1.12rem);line-height:1.65;color:var(--text);margin-top:clamp(28px,3.5vh,40px);">Quote text here.</p>
  <p style="font-size:clamp(0.78rem,1.05vw,0.95rem);color:var(--secondary);margin-top:10px;">— Attribution Name, Title, Organization</p>
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

**Animation:** Use the typewriter pattern (Pattern 14 in `references/css-animations.md`).
The correct wiring uses `.tw-pending` to hold the container at its full natural height
while text is invisible, measures `offsetHeight` after a 650 ms settle delay, then locks
that height before clearing `innerHTML` and calling `twTypewrite`. Do **not** use
`scrollHeight` measured at slide-enter time — it returns incorrect values for off-screen
`position:absolute` slides.

**Named example — Code Block with Typewriter:**
```json
{
  "id": "code-block-typewriter",
  "label": "Code Block with Typewriter",
  "category": "interactive",
  "css_deps": ["tw-cursor", "tw-pending"],
  "js_deps": ["twTypewrite"],
  "init_pattern": "enterCodeSlide / leaveCodeSlide via show()",
  "html": "<div id=\"cb{N}\" class=\"code-block\" style=\"font-size:clamp(0.78rem,1vw,0.92rem);\"><span class=\"kw\">SELECT</span>\n  ...</div>",
  "notes": "Replace cb{N} with a unique ID. Store innerHTML as cb{N}html before show(0). Wire enterCodeSlide/leaveCodeSlide into show() checking current/prev === slide_index."
}
```

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

**SVG arrow markers MUST use `markerUnits="userSpaceOnUse"`** to prevent markers from scaling with stroke-width. The SVG default `markerUnits="strokeWidth"` multiplies marker dimensions by the line's `stroke-width` value, producing oversized arrowheads (e.g., an 8x6 marker at `stroke-width="2"` renders at 16x12 user units). Always set `markerUnits="userSpaceOnUse"` so dimensions are absolute viewBox units. Use dimensions 10x7 with `refX="10" refY="3.5"` as the standard arrow marker size. Minimum gap between connected elements should be >= 14px to accommodate the marker without visual crowding. Each SVG diagram MUST define its own uniquely-named marker ID (e.g., `arr7`, `arr12`) — never reuse the same `id` (like `id="arrowhead"`) across multiple SVGs in the same HTML document, as duplicate IDs cause rendering conflicts where the browser uses whichever definition it finds first.

Standard marker template:
```html
<defs>
  <marker id="arrN" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto" markerUnits="userSpaceOnUse">
    <polygon points="0 0, 10 3.5, 0 7" fill="var(--accent)"/>
  </marker>
</defs>
```

Replace `arrN` with a unique ID per SVG (convention: `arr` + slide number, e.g., `arr7` for slide 7). Run `svg_calc.py marker --gap <px>` to compute marker dimensions for non-standard gap sizes.

**SVG viewBox MUST be tight to content bounds** — the gap between the last content element's bottom edge and the viewBox bottom should not exceed 12% of the viewBox height. Excessive bottom padding causes the diagram to render smaller than necessary. After placing all elements, set viewBox height to `max_content_bottom + 20px`. Run `svg_calc.py viewbox --elements "y1:h1,y2:h2,..."` to compute the correct height.

**SVG viewBox aspect ratio MUST be <= 2.5:1** (width:height). Diagrams wider than 2.5:1 render too small on 16:9 presentation slides because the browser preserves the SVG's aspect ratio and the available vertical space goes unused. For a diagram with many horizontal elements, increase the viewBox height (adding vertical padding or spacing) rather than widening the viewBox. Target a ratio between 1.5:1 and 2.2:1 for optimal rendering. If the diagram naturally needs to be wide (e.g., 3-column architecture), use a viewBox height of at least `width / 2.5`.

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

## Vertical Bar Chart
CSS flexbox bars sized by percentage. No coordinate math required.
Use for: quarterly comparisons, ranked values, before/after metrics.

```html
<div class="anim chart-v" style="width:100%;">
  <div style="display:flex;align-items:flex-end;justify-content:center;
    gap:clamp(12px,2vw,28px);height:clamp(140px,22vh,220px);
    border-bottom:1px solid var(--border);position:relative;">
    <div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;max-width:80px;">
      <span style="font-size:0.8rem;font-weight:600;color:var(--accent);">$4.2M</span>
      <div style="width:100%;height:62%;background:var(--accent);border-radius:6px 6px 0 0;"></div>
    </div>
    <!-- repeat for each bar; vary height % proportional to max value -->
  </div>
  <div style="display:flex;justify-content:center;gap:clamp(12px,2vw,28px);margin-top:8px;">
    <span style="flex:1;max-width:80px;text-align:center;font-size:0.75rem;color:var(--secondary);">Q1</span>
    <!-- repeat label for each bar -->
  </div>
</div>
```

- Set each bar's `height` as a `%` relative to the max value (max = 100%, others proportional).
- Use `background:var(--accent)` for the primary series; use `#10B981`, `#F59E0B` for multi-series.
- Wrap in a Two-Column Layout when pairing with a stat or bullet list.

---

## Horizontal Bar Chart
CSS flexbox bars sized by percentage width. Best when category labels are long or there are more than 5 categories.
Use for: ranking lists, survey results, feature adoption, multi-category comparisons.

```html
<div class="anim stagger chart-h" style="display:flex;flex-direction:column;gap:14px;width:100%;">
  <div style="display:flex;align-items:center;gap:16px;">
    <span style="min-width:120px;text-align:right;font-size:0.85rem;color:var(--secondary);">Category A</span>
    <div style="flex:1;height:28px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden;">
      <div style="height:100%;width:75%;background:var(--accent);border-radius:4px;"></div>
    </div>
    <span style="min-width:40px;font-size:0.85rem;font-weight:600;color:var(--text);">75%</span>
  </div>
  <!-- repeat row for each category -->
</div>
```

- Set each bar's `width` as a `%` of its max value.
- `class="anim stagger"` on the wrapper animates bars in sequence on slide enter.
- Vary bar color for emphasis: accent for the top/highlighted row, `rgba(255,255,255,0.25)` for others.

---

## Line / Area Chart
Inline SVG using `<polyline>` (line only) or `<polygon>` (filled area beneath the line).
Use for: trends over time, growth curves, before/after comparisons across periods.

```html
<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-height:40vh;">
  <defs>
    <linearGradient id="areaFillN" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="var(--accent)" stop-opacity="0.0"/>
    </linearGradient>
  </defs>
  <!-- optional grid lines -->
  <line x1="0" y1="40" x2="600" y2="40" stroke="var(--border)" stroke-width="1"/>
  <line x1="0" y1="100" x2="600" y2="100" stroke="var(--border)" stroke-width="1"/>
  <line x1="0" y1="160" x2="600" y2="160" stroke="var(--border)" stroke-width="1"/>
  <!-- filled area: close polygon to bottom corners -->
  <polygon points="0,160 120,130 240,80 360,50 480,30 600,20 600,180 0,180"
    fill="url(#areaFillN)"/>
  <!-- line on top -->
  <polyline points="0,160 120,130 240,80 360,50 480,30 600,20"
    fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
  <!-- data point dots -->
  <circle cx="0" cy="160" r="4" fill="var(--accent)"/>
  <circle cx="120" cy="130" r="4" fill="var(--accent)"/>
  <!-- x-axis labels -->
  <text x="0" y="198" text-anchor="middle" fill="#666" font-size="12">Jan</text>
  <text x="120" y="198" text-anchor="middle" fill="#666" font-size="12">Feb</text>
</svg>
```

- Replace `areaFillN` with a unique gradient ID per slide (e.g., `areaFill7` for slide 7).
- **Y-coordinate formula:** `y = chart_bottom - (value / max_value) × chart_height`. For a 180px chart area (bottom at y=180): `y = 180 - (value / max_value × 180)`.
- Use `<polyline>` alone (drop the polygon) for a line-only chart without fill.
- For a second series add another polyline in a contrasting color (e.g., `#10B981`).

---

## Donut Chart
SVG `stroke-dasharray` technique. One `<circle>` per segment positioned by offset.
Use for: part-to-whole proportions, market share, budget allocation (2–5 segments max).

```html
<div class="anim" style="display:flex;align-items:center;gap:40px;justify-content:center;width:100%;">
  <svg viewBox="0 0 200 200" style="width:clamp(140px,18vw,200px);height:clamp(140px,18vw,200px);flex-shrink:0;">
    <!-- circumference of r=80: 2π×80 ≈ 502.65 -->
    <!-- Segment 1: 60% → arc = 301.6; starts at top via rotate(-90) -->
    <circle cx="100" cy="100" r="80" fill="none"
      stroke="var(--accent)" stroke-width="28" stroke-linecap="butt"
      stroke-dasharray="301.6 502.65"
      stroke-dashoffset="0"
      transform="rotate(-90 100 100)"/>
    <!-- Segment 2: 25% → arc = 125.66; offset = -301.6 -->
    <circle cx="100" cy="100" r="80" fill="none"
      stroke="#10B981" stroke-width="28" stroke-linecap="butt"
      stroke-dasharray="125.66 502.65"
      stroke-dashoffset="-301.6"
      transform="rotate(-90 100 100)"/>
    <!-- Segment 3: 15% → arc = 75.4; offset = -(301.6+125.66) = -427.26 -->
    <circle cx="100" cy="100" r="80" fill="none"
      stroke="#F59E0B" stroke-width="28" stroke-linecap="butt"
      stroke-dasharray="75.4 502.65"
      stroke-dashoffset="-427.26"
      transform="rotate(-90 100 100)"/>
    <!-- center label -->
    <text x="100" y="95" text-anchor="middle" fill="white" font-size="28" font-weight="700">60%</text>
    <text x="100" y="118" text-anchor="middle" fill="#666" font-size="12">Primary</text>
  </svg>
  <!-- legend -->
  <div style="display:flex;flex-direction:column;gap:12px;">
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="width:12px;height:12px;border-radius:2px;background:var(--accent);flex-shrink:0;"></div>
      <span style="font-size:0.875rem;color:var(--text);">Segment A — 60%</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="width:12px;height:12px;border-radius:2px;background:#10B981;flex-shrink:0;"></div>
      <span style="font-size:0.875rem;color:var(--text);">Segment B — 25%</span>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      <div style="width:12px;height:12px;border-radius:2px;background:#F59E0B;flex-shrink:0;"></div>
      <span style="font-size:0.875rem;color:var(--text);">Segment C — 15%</span>
    </div>
  </div>
</div>
```

**Segment math** (circumference C = 2π × r; for r=80, C ≈ 502.65):
- Arc length for segment = `(percentage / 100) × C`
- `stroke-dasharray` = `arc_length C`
- `stroke-dashoffset` for segment N = `-(sum of all previous arc lengths)`
- All circles use `transform="rotate(-90 cx cy)"` so segment 1 starts at the top (12 o'clock)

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
