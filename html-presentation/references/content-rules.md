# Content Rules

## Always Apply (Rules 1–13)

1. **One idea per slide.** If you have two points, make two slides
2. **Aim for ~30 words per slide.** Slides are visual aids, not documents. Guideline, not hard limit — some slides (comparison panels, step flows) may need more.
3. **Every slide has a visual component.** No exceptions. Card Grids, Icon+Label Lists, Stat Callouts, CTA Blocks, and all catalog components qualify. Slide with only `<h2>` + `<p>` text — no component — is not allowed. See `references/visual-components.md`
4. **Consistent accent color.** Pick one accent and use for all highlights, buttons, and emphasis
5. **No bullet point dumps.** If you need bullets, use an Icon + Label List component instead
6. **Big text beats small text.** When in doubt, make it bigger
7. **Use full viewport efficiently.** Set `max-width: min(1600px, 96vw)`, use `clamp()`-based padding so content fills available space. Projectors and wide monitors have room — don't waste it with oversized margins. Keep breathing room *between* elements; goal is balanced density, not clutter.
8. **Use Google Material Symbols instead of emojis.** Load via `<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded&display=block" rel="stylesheet">`. Use `<span class="material-symbols-rounded">icon_name</span>`. Endpoint MUST be `css2?family=Material+Symbols+Rounded` (NOT the old `icon?family=Material+Icons+Round`), class MUST be `material-symbols-rounded`.
9. **Use CSS animations when they aid presentation.** Entrance animations (fade-in, stagger) on every slide's primary content. Avoid looping animations on static slides. Always respect `prefers-reduced-motion`. See `references/css-animations.md` for approved patterns and rules.
10. **Use CSS illustrations, SVG shapes, and gradients for visual elements.** Do not rely solely on Material Symbols. All image visuals must be inline — no external image assets (Material Symbols CDN is only permitted external dependency). Keep total file size under 2MB. No embedded images: under 500KB ideal. When images embedded via `embed_image.py`, exceeding 500KB is acceptable.
11. **No double bullets.** When list items use a leading symbol, emoji, or icon, parent `<ul>` MUST set `list-style: none; padding: 0;` to suppress default bullet.
12. **Left-align bulleted lists — or drop the bullets.** All `<ul>` and `<ol>` with bullet markers MUST use `text-align: left`. When list lives inside centered container, explicitly set `text-align: left` on list element.
13. **Clickable links open in new tab with presentation-friendly styling.** All `<a>` tags MUST include `target="_blank" rel="noopener"`. Style with accent color underline: `a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--accent); transition: color 0.2s; } a:hover { color: var(--accent); }`

## Apply When Relevant (Rules 14–20)

> Skip rules in this section that don't apply to your deck. Each rule lists its condition.

14. **QR code appendix slide.** [CONDITION: only if deck has `<a>` links to external URLs] `python scripts/run_script.py generate_qr_appendix.py <deck.html>` after building. Script is idempotent. QR codes MUST use black modules on white background. **Max 6 QR codes per appendix slide.** If more than 6 external links, split across multiple appendix slides. (Auto-enforced by `generate_qr_appendix.py` — slide authors don't need to track.)
15. **Architecture and flow diagrams must be full-width and readable.** [CONDITION: only when building slides with architecture/flow diagrams] SVG diagrams with 4+ nodes, branching paths, or multi-level structure MUST use **full-width layout** — never in two-column grid where it gets half the slide. Use one of these layouts:
    - **Full-width diagram** (SVG spans slide width, `width="100%"` or `width="720"`) with compact 2-column icon list *below*.
    - **Diagram-only slide** where architecture is entire content with labels embedded in SVG.
    - Two-column only acceptable for simple, linear diagrams where each element is readable at half-slide width.
    Minimum readable sizes: node box height >= 36px; label `font-size` >= 12 (viewBox units); connector arrow >= 16px. If diagram needs text < 12px to fit in column, MUST promote to full-width.
16. **SVG layout integrity — five hard rules.** [CONDITION: only when building slides with inline SVG]
    - **No overlapping rects.** For each column of stacked `<rect>` boxes, verify `y_N + height_N < y_(N+1)` before writing. Overlapping boxes silently clip text. Min 10px gap between boxes.
    - **No rotated text.** `transform="rotate(...)"` on `<text>` almost always means container too narrow. Fix by widening container, using multi-line label, or redesigning as readable box.
    - **SVG `max-height` >= 58vh.** Lower values render too small, leave large empty bands. Use at least `58vh`; `65vh` preferred for full-width architecture diagrams.
    - **viewBox height must contain all content with 20px to spare.** Identify lowest element, compute `y + height`. viewBox height MUST be at least that value plus 20px. Never set equal to last element's bottom edge — 1px overrun clips silently.
    - **Use `svg_calc.py` before writing any SVG with stacked boxes or multi-column layout.** Never do coordinate math manually. Commands: `stack` (y positions), `textbox` (min rect width), `distribute` (cx values), `viewbox` (required height), `arrow` (connector path), `grid` (full x/y table), `layout` (complete flow from JSON). Example: `python scripts/run_script.py svg_calc.py stack --count 4 --box-height 48 --gap 16`
17. **When removing stat card from grid, update column count.** [CONDITION: only when modifying an existing stat card grid] Dropping card from `grid-template-columns:repeat(4,1fr)` without updating repeat leaves remaining cards stretched. Always update `repeat(N,1fr)` to match actual card count.
18. **Wrong is 3× worse than unknown — omit unconfirmed facts.** [CONDITION: especially critical when deck includes customer-specific stats or `[INFERRED]` facts] If customer-specific figure or `[INFERRED]` fact can't be confirmed, remove entirely. Omission safer than wrong number — wrong numbers appear in 5–7 places at once. When in doubt, say "we're exploring this" rather than stating unverified figure.
19. **SVG diagram boxes must be sized to fit their text — never guess.** [CONDITION: only when building slides with inline SVG] Run `python scripts/run_script.py svg_calc.py textbox --text "your label" --font-size 12` to get exact minimum box width before writing `<rect>`. Default >= 200px for any box with function name, SQL keyword, or long token (e.g., `SYSTEM$STREAM_HAS_DATA()`). Add at least 24px horizontal padding. Expand `viewBox` width to match — never clip label. For single-column flow diagrams, `viewBox="0 0 260 H"` with `cx=130` is safe default.
20. **Executive decks use BLUF structure and action titles.** [EXEC MODE ONLY — skip if `exec_mode: false`] When `exec_mode` true:
    - Every `<h2>` title MUST be **declarative assertion** — sentence stating conclusion, not noun label.
      - BAD: `"Data Architecture"` → GOOD: `"Snowflake Eliminates Data Silos Without Migration Risk"`
      - BAD: `"Key Benefits"` → GOOD: `"Three Capabilities That Directly Reduce Your Cost Per Query"`
    - Executive Summary slide (s2): high-impact component — CTA Block, Stat Callout, or similar — one bold statement, one supporting line, key metric if available. No bullets. No context before this slide.
    - **Cap at 7 content slides.** If content won't fit, cut it — never add slides.
    - **Skip Agenda entirely.** Executives prefer to reach the point immediately.
