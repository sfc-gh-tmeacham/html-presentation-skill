---
name: html-presentation
description: "Generate beautiful self-contained HTML presentations with rich visual components. Use when: html presentation, html slides, html deck, html slide deck, self-contained presentation. Do NOT use for PowerPoint, Google Slides, or PPTX requests."
---

# HTML Presentation

## ⚠️ Shell Safety Rules — Read Before Issuing Any Bash Command

These rules apply **everywhere** in this skill. Violating them causes the shell to hang and blocks the user.

**NEVER do any of these:**
- `<<EOF` or `<<'EOF'` heredoc syntax — the shell gets stuck waiting for the terminator
- `python3 -c "..."` or `python -c "..."` with multi-line strings — use a script file instead
- Multi-line `while read` loops in bash
- `bash -c "..."` with embedded newlines
- Any bash command that spans multiple lines inside a single string

**ALWAYS do these instead:**

| Instead of... | Do this |
|---|---|
| `python3 -c "import re\n..."` | Use the `write` tool to save a `.py` file, then `python3 /tmp/script.py` |
| Inline logic over multiple lines | `python scripts/run_script.py <script.py> [args]` |
| Multi-step bash chains | Separate sequential bash tool calls |

Every bash command in this skill must be **a single line**. If it cannot be expressed that way, write a Python script first, then call it.

---

## Workflow

### Step 0: Resume Check

Before doing anything else, check whether a prior run was interrupted. The presentation folder follows this structure:

- **With customer**: `[customer-slug]/[topic-slug]/` (e.g., `acme/cortex-ai/`)
- **No customer**: `[topic-slug]/` (e.g., `cortex-ai/`)

Look for checkpoint files inside the presentation folder:

- `[folder]/[topic-slug]-brief.md` — research brief with sourced, tagged facts (means Step 1 research is done)
- `[folder]/[topic-slug]-plan.md` — approved slide plan (means Step 2 is done; proceed directly to Step 3)
- `[folder]/[topic-slug]-[audience-slug]-slides.html` — HTML file exists (means build is done; proceed to Step 5)

If checkpoint files exist, read them and resume from the furthest completed step. Inform the user: "Found a prior checkpoint — resuming from Step N."

If no checkpoint files exist, proceed normally from Step 1.

---

### Step 1: Gather Content

Ask the user for:
- **Topic** and audience
- **Customer** -- is this presentation for a specific customer? If yes, ask for the customer name. Use the customer name in the title slide subtitle and personalize examples throughout the deck to reference their context.
- **Industry** -- is this presentation for a particular industry? If yes, present these options (single-select): Advertising, Media & Entertainment / Financial Services / Healthcare & Life Sciences / Manufacturing / Public Sector / Retail & Consumer Goods / Technology / Telecom / Other. If "Other", ask them to specify. Use the selected industry to tailor examples, use cases, terminology, and icons throughout the deck.
- **Slide count preference** (or auto-pick: simple = 5-7, complex = 10-15+, max 30)
- **Key points** they want to cover (or offer to suggest based on topic)
- **Brand/accent color** (or auto-select from `references/accent-colors.md`)
- **Speaker notes** -- yes or no
- **Title slide logo** -- offer three options: (1) Snowflake logo (`assets/snowflake-logo.svg`), (2) a different logo they provide, or (3) no logo. If they choose option 2, collect the file path (or let them paste/attach the image in a follow-up message).
- **Custom graphics** -- any additional logos, screenshots, or diagrams to include beyond the title slide logo? Advise the user that images with a transparent background work best. Accept file paths to PNG, JPG, SVG, or other image formats — or the user can paste images directly into the chat.
- **Presenter slide** -- would they like to include a presenter slide? If yes, ask how many presenters there are, then gather for each: (1) full name, (2) title/role. Optionally ask if they'd like to include a headshot photo for each presenter — they can provide a file path **or paste the image directly into the chat**. The presenter count determines the layout (see Presenter slide visual rules). The presenter slide does NOT count toward the slide count max.
- **Executive audience** -- is this presentation for an executive audience (VP, C-suite, board, or key decision-makers)? If yes, set `exec_mode: true` — this activates BLUF structure: the recommendation comes first, the Agenda slide is skipped, slide titles become declarative assertions, and the deck is capped at 7 content slides. See Step 2 and Content Rules for full details.

**Handling the title slide logo:**
- **Snowflake logo**: Note that you will place a `{{SNOWFLAKE_LOGO}}` placeholder in the HTML during Step 3 — the embed phase handles the rest. Do NOT attempt to write any SVG now.
- **Custom logo (SVG)**: Use a `{{SVG_INLINE:path}}` placeholder (standalone token, not inside `<img>`). If sizing is needed, pass CSS as the second arg: `{{SVG_INLINE:path|height:60px;display:block;margin:0 auto}}`. See `references/graphics-embedding.md`.
- **Custom logo (raster)**: Use a `{{IMG:path}}` placeholder inside an `<img src="...">` tag.
- **No logo**: Omit any logo element from the title slide entirely.

**Handling images — ask_user_question limitation:** The structured question tool (ask_user_question) only supports text input and multiple-choice options — users **cannot** paste images through it. When asking about headshots or custom graphics:
- Do NOT try to collect image paths via ask_user_question. Instead, mention in the question text that the user can provide a file path now OR paste/attach the image in a follow-up message after answering the other questions.
- Example phrasing: "For your headshot, you can type a file path here, or just paste/drop the image in your next message (type 'done' or any text along with the image so you can press Enter)."

**Handling pasted images:** When a user pastes an image directly into the chat (instead of providing a file path), save it to the presentation folder so the build scripts can process it:
1. Write the pasted image data to: `[folder]/pasted_<purpose>_<timestamp>.png` (e.g., `acme/cortex-ai/pasted_headshot_1711700000.png`)
2. For **raster images**: use `{{IMG:path}}` in `<img src="...">` tags; for **SVG files**: use `{{SVG_INLINE:path}}` as a standalone token.
3. For presenter headshots, use that path with `insert_presenter.py --photo`.
4. Inform the user: "Got it — I've saved your pasted image to the presentation folder."

**Handling user-provided image file paths:** When the user provides a path to an image file, copy it into the presentation folder before use:
1. Copy the file to `[folder]/` (preserving the original filename)
2. Use the new `[folder]/filename` path in all subsequent references
3. Inform the user: "Copied `filename` to the presentation folder."

If the user provides a document, transcript, or notes, extract these elements automatically and propose defaults for each field above.

**After gathering topic and customer, create the presentation folder:**

- Derive `[topic-slug]` from the topic (lowercase, hyphen-separated, e.g., `cortex-ai-overview`)
- Derive `[customer-slug]` from the customer name if provided (lowercase, hyphen-separated, e.g., `acme-corp`)
- Derive `[audience-slug]` from the audience description (lowercase, hyphen-separated, max 2–3 words, e.g., `exec`, `engineering-team`, `sales-leadership`, `all-hands`)
- Create the folder: `[customer-slug]/[topic-slug]/` if a customer was given, otherwise `[topic-slug]/`
- All artifacts for this presentation (brief, plan, HTML, images) will be written to this folder
- Inform the user: "Created presentation folder: `[folder-path]`"

**⚠️ MANDATORY STOPPING POINT**: You MUST present these questions to the user and wait for their answers before proceeding. Do NOT skip ahead to planning or building. Even if the user's initial message implies a topic, you must still confirm all ten items (topic/audience, customer, industry, slide count, key points, accent color, speaker notes, custom graphics, presenter slide, executive audience) with the user before moving to Step 2.

**Image collection follow-up:** After the user answers the Step 1 questions, check if they indicated they want to include images (headshots, logos, screenshots, etc.) but did NOT yet provide a file path or paste an image. If any images are still outstanding, prompt the user **before** moving to Step 2:
- "You mentioned you'd like to include [a headshot / a logo / custom graphics]. Go ahead and paste or drop the image(s) here (type any text like 'here you go' along with it so you can press Enter), or provide a file path. I'll wait before moving on to the slide plan."
- Do NOT proceed to Step 2 until all referenced images have been received (as a pasted image or a file path) or the user explicitly says to skip them.

### Research Subagent (optional — knowledge-heavy topics)

If the topic is knowledge-driven (technology, business case, data analysis, product capabilities) and the user did **not** supply their own notes, document, or transcript, launch a `general-purpose` subagent **before** Step 2 to build a factual brief. Skip this if the user provided their own content.

**Before launching**, inform the user: "Researching your topic — this may take a minute or two."

**Subagent type:** `general-purpose` | **readonly:** `true`

Prompt:
```
Research the following topic for a presentation and return a structured brief.

Topic: [TOPIC]
Audience: [AUDIENCE]
Key points to cover: [KEY_POINTS]

## Accuracy rules (read carefully before writing anything)

**Wrong is 3× worse than unknown.** Do not guess. If you are not confident in a fact, label it
`[INFERRED]` or omit it entirely. A slide that says "we're not sure of the exact figure" is
recoverable. A slide with a wrong number in front of a customer is not.

Label every fact, statistic, example, and quote with one of two tags:
- `[EXTRACTED]` — the information was stated directly in a source you can cite (verbatim or
  close paraphrase). Include the source inline: `[EXTRACTED] (Source: Name, Year/URL)`
- `[INFERRED]` — the information is your synthesis, estimation, or logical inference from
  multiple sources. Include a brief basis: `[INFERRED] (Basis: derived from X and Y)`

For any statistic about a specific named organization (account counts, employee headcount,
revenue, data volumes, growth percentages), ALSO prefix it with `[UNVERIFIED — confirm with
customer]` regardless of its EXTRACTED/INFERRED tag.

If you cannot find a credible source for a claim, say so explicitly rather than inventing one.

Return:
1. 3–5 compelling statistics or data points — each tagged [EXTRACTED] or [INFERRED] with citation
2. 2–3 concrete real-world examples or case studies — each tagged with source
3. 1–2 strong quotes from credible sources — [EXTRACTED] only; do not fabricate quotes
4. Key terminology or concepts the audience needs to know
5. Common objections or questions the audience may raise
6. Suggested narrative arc: problem → insight → solution → outcome

If `exec_mode` is true: restructure the narrative arc as **conclusion → evidence → context** (BLUF
order). The executive already knows the problem — lead with the recommendation, then prove it, then
provide context only if needed.

Be specific. Format as a structured markdown brief. Do not write slide copy — only gather raw material.
```

Use the returned brief as the factual foundation for slide copy in Step 2.

**⚠️ Accuracy calibration — wrong is 3× worse than unknown:** Before using any fact from the brief in slide copy, check its tag:
- `[EXTRACTED]` facts may be used directly; cite the source in speaker notes.
- `[INFERRED]` facts must be presented to the user for confirmation before being written into slide copy.
- `[UNVERIFIED — confirm with customer]` facts MUST be confirmed by the user during Step 2 before being placed in the deck. A wrong stat is costly to fix because it typically appears in multiple places: stat cards, SVG `<text>` labels, speaker notes, tooltips, and bullet lists. **If a fact cannot be confirmed, omit it — never use the researched estimate.**

**Checkpoint:** Save the full brief (with all tags and citations intact) to `[folder]/[topic-slug]-brief.md` immediately after the subagent returns. This file is a citable research artifact — do not strip or summarize the tags and sources when saving.

**URL validation (mandatory after saving brief):** Extract every URL from the brief and verify it resolves. Run:
```bash
python scripts/run_script.py validate_urls.py [folder]/[topic-slug]-brief.md
```
For any URL that returns a non-200 status or times out:
1. Mark it `[DEAD LINK]` inline in the brief file
2. Do NOT use it as a citation in slide copy or speaker notes
3. If the source is the only citation for a key fact, downgrade that fact from `[EXTRACTED]` to `[INFERRED]` and note the dead link

This validation runs on the brief — the HTML link validation in Step 3 is a separate check on links written into the deck itself.

### Step 2: Plan the Slide Deck

Map each slide to a visual component (see `references/visual-components.md`). Present the plan:

```
Slide 1: Title -- "Topic Name" with subtitle + accent gradient
Presenter: [if requested] Name, title, and optional headshot for each presenter (does not count toward slide max)
Agenda: Icon + Label List of thematic sections (does not count toward slide max)
Slide 2: Setup -- Frame the problem or context
Slide 3: Core -- Card Grid with 3 key concepts
Slide 4: Core -- Step Flow showing the process
...
Slide N: Takeaway -- Stat Callout + call to action
```

**⚠️ MANDATORY STOPPING POINT**: Present the slide plan to the user. Do NOT proceed to Step 3 until user explicitly approves.

**Executive deck plan (exec_mode):** When `exec_mode` is true, use this BLUF-first structure instead of the standard flow:

```
Slide 1: Title -- "Topic Name" with subtitle + accent gradient
Presenter: [if requested] (does not count toward slide max)
Slide 2: Executive Summary -- BLUF: state the recommendation or key conclusion directly (use CTA Block or Stat Callout — no bullets)
Slide 3: Context -- ONE slide max: brief "why this matters" (not a full setup sequence)
Slide 4–6: Supporting Evidence -- Prove the recommendation with data, comparisons, or examples
Slide 7: Call to Action -- Specific ask with a clear next step and owner
```

Executive deck rules:
- **Cap at 7 content slides.** Executives do not read long decks — if content cannot fit in 7 slides, cut it, don't add slides.
- **No Agenda slide.** Skip it entirely — executives prefer to reach the point immediately.
- **No setup/problem-framing before the BLUF.** Slide 2 is always the recommendation, not the context.

**Checkpoint:** Once the user approves, save the full slide plan to `[folder]/[topic-slug]-plan.md` before starting the build.

### Step 3: Build the HTML

Generate a single self-contained HTML file following the Slide Structure, HTML Output, and Content Rules sections below. Every slide MUST have a visual component from `references/visual-components.md`.

**Before starting**, inform the user: "Building your slide deck — this may take a few minutes while I read the reference files and generate all the slides."

**Always build directly in the main context** — do not delegate HTML generation to a subagent. Before writing, read all four reference files:
- `references/visual-components.md`
- `references/css-animations.md`
- `references/accent-colors.md`
- `references/graphics-embedding.md`

**Inlining the Snowflake logo (if selected in Step 1):** Place a bare `{{SNOWFLAKE_LOGO}}` token on its own line as the **first child inside `.slide-inner`** on the title slide (before the `<h3>` eyebrow). The `embed_image.py` embed phase will replace it with the correct inline `<svg>` block automatically — do NOT read any SVG file, do NOT write any `<svg>` or `<path>` markup manually.

**Iterative Batch-Build (required for 13+ slides):**

Large decks written in a single `write` call risk context timeouts — a partial write is worse than no file. Instead, always use the batch approach:

1. **Batch 1 — Shell + first slides**: Write the complete HTML structure (all `<head>`, CSS, opening `<div id="deck">`) plus slides **s1 through s10** (or fewer if the deck is shorter). Close with a placeholder comment before the closing tags:
   ```html
   <!-- SLIDES_REMAINING -->
   
   </div><!-- end #deck -->
   <div class="counter"></div>
   <div id="nav">...</div>
   <script>...</script>
   </body></html>
   ```
   The `<span id="total">` counter should reflect the **final** slide count (including all planned batches) even in Batch 1 — the JS is already correct from the start.

2. **Batch 2 — Next slides**: Use `edit` to replace `<!-- SLIDES_REMAINING -->` with the next batch of slides (s11–s20) plus a new placeholder:
   ```html
   [s11 ... s20 HTML]
   
   <!-- SLIDES_REMAINING_2 -->
   ```

3. **Subsequent batches**: Repeat — each `edit` replaces the latest `<!-- SLIDES_REMAINING_N -->` placeholder with the next batch of ~10 slides plus a new placeholder (or nothing for the final batch).

4. **Final batch**: The last `edit` replaces the final placeholder with the remaining slides and **no new placeholder**. The file is now complete.

**Batch sizing guideline:** Size batches by complexity, not just count:
- **5 slides per batch** when the batch includes 2+ SVG-heavy slides (architecture diagrams, step flows, inline SVG illustrations)
- **10 slides per batch** for simpler content (card grids, stat callouts, quotes, icon lists)

When in doubt, use 5. Smaller batches add one extra `edit` call but prevent losing a large amount of work to a context timeout mid-write.

**For decks of 12 slides or fewer:** A single `write` call is fine — use the standard approach.

**Mark each batch complete in the todo list** before starting the next (`system_todo_write` with status `completed`), so progress is preserved if the session is interrupted. Resume from the last completed batch using the `<!-- SLIDES_REMAINING_N -->` placeholder as the insertion point.

**Two-phase build (when the deck includes user-provided images, SVGs, or the Snowflake logo):**
1. **Author phase** — Write the HTML with placeholder tokens. Do NOT write any `<svg>`/`<path>` markup or base64 strings during this phase.
   - `{{SNOWFLAKE_LOGO}}` — standalone token for the Snowflake logo on the title slide
   - `{{SVG_INLINE:path}}` or `{{SVG_INLINE:path|css-style}}` — standalone token for any user-provided `.svg` file
   - `{{IMG:path}}` or `{{IMG:path|max-px}}` — inside `<img src="...">` for raster images (PNG/JPG/etc.)
2. **Embed phase** — Inform the user: "Embedding images — this may take a moment." Then run `python scripts/run_script.py embed_image.py <deck.html>` to resolve all tokens. This happens entirely in Python — no SVG markup or base64 data ever enters the conversation context.
3. **QR appendix phase** — If the deck contains any `<a>` links to external URLs, inform the user: "Generating QR code appendix." Then run `python scripts/run_script.py generate_qr_appendix.py <deck.html>` to scan for links and append a QR code appendix slide with inline SVG QR codes. The script auto-numbers the new slide and updates the total counter. **The script requires a `<div class="counter"></div>` marker in the HTML** to know where to insert the new slide — this MUST be included in the initial HTML build (see HTML Output > Navigation).

If the deck has no user-provided images, no SVGs, and no Snowflake logo (only Material Icons, inline CSS graphics), skip the embed phase — the HTML is already self-contained.

**4. URL validation phase** — After the QR appendix is generated, verify that every external link in the deck resolves successfully. Run:
```bash
python scripts/run_script.py validate_urls.py [folder]/[topic-slug]-[audience-slug]-slides.html
```
Any URL returning a non-200 status MUST be replaced with a live equivalent before proceeding. After fixing any broken URLs, re-run `generate_qr_appendix.py` — it is idempotent and will rebuild QR codes to encode the corrected links. Do not proceed to Step 4 with unresolved broken links.

For all image/graphics technical details, see `references/graphics-embedding.md`.

**Slide ID and numbering rules:**
- Every slide (including Agenda and Presenter) MUST have a sequential `id="sN"` attribute starting from `s1` for the title slide.
- The Agenda slide and Presenter slide are real slides in the HTML with their own IDs, even though they don't count toward the content slide plan.
- The `<span id="total">` counter in the navigation MUST equal the actual number of slide divs in the HTML.
- When adding or removing slides after initial generation, ALL subsequent slide IDs must be renumbered to stay sequential and the total must be updated. **Always renumber in reverse order** (highest ID first, working down) to avoid double-replacement bugs. Use `scripts/insert_presenter.py` via `run_script.py` to automate post-build presenter slide injection (it handles resize, base64, insertion, renumbering, and total update in one step).

### Step 4: Save and Preview

Save the file as `[folder]/[topic-slug]-[audience-slug]-slides.html`.

Open in the default browser:
```bash
open [folder]/[topic-slug]-[audience-slug]-slides.html
```

If `open` fails, try `xdg-open` (Linux) or provide the file path for manual opening.

### Step 5: Verify

**Validation Subagent:**

Inform the user: "Validating the deck — this may take a minute." Then delegate the automated validation and fix cycle to a subagent — this keeps error output and large HTML reads out of the main context.

**Subagent type:** `general-purpose` | **readonly:** `false`

Prompt:
```
Validate and fix the HTML slide deck at: [folder]/[topic-slug]-[audience-slug]-slides.html

Step 1: Run the validator with context enabled:
  python scripts/run_script.py validate_deck.py [folder]/[topic-slug]-[audience-slug]-slides.html --context 5

  The `--context 5` flag prints ±5 lines around each warning/failure, with any base64
  content automatically redacted to `[base64 data omitted — Nkb]`. This gives you all
  the context needed to make each fix. **Do NOT use the Read tool to open the HTML file
  directly** — the validator output is sufficient and avoids base64 flooding your context.

Step 2: For each reported issue, apply the fix using the Edit tool with the exact
  surrounding text shown in the context snippet. Each message includes a slide ID and
  line number (e.g. `s10 line 450 →`) to pinpoint the location.

Step 3: Re-run the validator with --context 5. Repeat until it passes or until you have made 3 fix attempts.

Return a one-line summary: "PASS — N slides, all checks clean" or "Fixed N issues: [brief list]". If validation still fails after 3 attempts, list the remaining errors.
```

Then manually verify:
- Accent color is consistent across all slides
- Material Icons render correctly (not showing as text)
- Animations fire on slide enter
- Navigation works (arrow keys, slide counter visible)
- **All external links return HTTP 200** — re-run the URL validation phase if this was skipped or if any links were added during iteration
- **SVG diagrams (check each slide with an inline SVG):**
  - No two `<rect>` elements in the same column overlap — confirm `y + height` of each box is less than `y` of the next
  - No `<text transform="rotate(` present — rotated text signals a layout problem
  - `max-height` on SVG containers is ≥ 58vh — lower values cause excess empty slide space
  - No unverified customer facts in `<text>` elements — SVG text is easy to overlook during review. Grep for numbers and proper nouns inside `<text>` tags and confirm they match user-verified data

If any check fails, fix the HTML and re-preview before proceeding.

### Step 6: Iterate

Ask: "Please take a moment to carefully review the full presentation. Let me know about any changes you'd like — for example: wording or copy edits on any slide, adding or removing slides, rearranging the slide order, additional custom graphics or images, color or styling tweaks, or anything else. I'm happy to iterate until it's exactly right."

**⚠️ MANDATORY STOPPING POINT**: Wait for user feedback before making changes.

**Common iteration patterns and their implications:**
- **Wording / copy edit**: Edit the slide HTML directly. Re-run the validator if the change touches a list, link, or SVG `<text>` element.
- **Add a slide**: Insert the new slide HTML, renumber all subsequent `id="sN"` attributes in reverse order (highest first), update `<span id="total">`, and re-run the validator.
- **Remove a slide**: Same renumbering as above. If the removed slide was in a stat card grid, also update `grid-template-columns:repeat(N,1fr)` to match the new card count.
- **Change accent color**: Global find-replace the old hex value with the new one across the entire file. Check that SVG fills and stroke colors using the accent are also updated.
- **Add/remove an external link**: Re-run `generate_qr_appendix.py` — it is idempotent and will rebuild the QR appendix to match the current link set.
- **Any structural change**: Re-run `validate_deck.py --context 5` before presenting the updated deck.

---

## Slide Structure

Every deck follows this proven flow:

| Slide | Purpose | Content |
|-------|---------|---------|
| **1. Title** | Set the stage | Big title, subtitle, your name or brand |
| **2. Setup** | Frame the problem or context | Why this matters, what the audience will learn |
| **3-8. Core Content** | Deliver the meat | One idea per slide, each with a visual component |
| **9. Evidence** | Prove your point | Stats, quotes, case studies, examples |
| **10. Takeaway** | Land the message | Summary, call to action, next steps |

Adjust the number of core content slides based on topic complexity. Simple topics: 5-7 total slides. Complex topics: 10-15 slides. Never exceed 30 slides.

**Executive Deck Structure (exec_mode):** When `exec_mode` is true, replace the standard flow with the following:

| Slide | Purpose | Content |
|-------|---------|---------|
| **1. Title** | Set the stage | Big title, subtitle, your name or brand |
| **2. Executive Summary** | **BLUF — lead with the conclusion** | The recommendation or key takeaway, stated directly. Use a CTA Block or Stat Callout. No bullets, no build-up. |
| **3. Context** | Brief "why this matters" (1 slide max) | Background or problem framing — keep it tight |
| **4–6. Supporting Evidence** | Prove the recommendation | Data, comparisons, case study, or key metrics |
| **7. Call to Action** | Specific ask | Clear next step, owner, and timeline |

Cap executive decks at **7 content slides**. No Agenda slide.

**Presenter Slide (optional):** If the user requests a presenter slide, include it immediately after the Title slide (before the Agenda). The Presenter slide does NOT count toward the slide count max.

**Presenter slide visual rules:**
- If there is **one presenter**: use a centered layout with the optional headshot above the name and title. The headshot should be displayed in a circle (`border-radius: 50%`, `width: clamp(100px, 12vmin, 160px)`, `height: clamp(100px, 12vmin, 160px)`, `object-fit: cover`) with a subtle accent-colored ring border (`border: 3px solid var(--accent)`). Name in bold white (`clamp(1.5rem, 2.5vw, 2.25rem)`), title in secondary color (`clamp(1rem, 1.5vw, 1.5rem)`) below.
- If there are **two presenters**: use a two-column side-by-side layout, each column centered with circular headshot, name, and title.
- If there are **three or more presenters**: use a card grid (2 or 3 columns) with one card per presenter. Maximum of 9 presenters — `insert_presenter.py` will error if this limit is exceeded.
- If **no headshot is provided** for a presenter, display a Material Icon placeholder (`person` icon, `clamp(3rem, 5vw, 4.5rem)`, accent-colored) inside the circle instead.
- Stagger the card/column animations for sequential reveal.
- The heading should be a small uppercase `h3` label ("Presented By" or "Your Presenters") with the accent color.
- **All presenter headshots MUST be circularly cropped using CSS** (`border-radius: 50%; object-fit: cover; width/height equal`). Do NOT pre-crop the source image.
- Headshot images must be processed through the Graphics Embedding Rules (see `references/graphics-embedding.md`).

For HTML patterns, see the **Presenter Slide** section in `references/visual-components.md`.

**Agenda Slide (mandatory):** Every deck MUST include an Agenda slide immediately after the Title slide (or after the Presenter slide, if present). The Agenda does NOT count toward the slide count max. List 3-6 thematic sections (not every individual slide).

**Agenda visual rules:**
- Use a **numbered grid of cards** (2 or 3 columns), one card per section
- Each card gets: a Material Icon (accent-colored, `clamp(1.5rem, 2.5vw, 2rem)`), a bold section title (`clamp(0.9rem, 1.4vw, 1.2rem)` white), and a one-line descriptor (`clamp(0.75rem, 1.1vw, 1rem)` secondary color)
- Cards use the standard card style (`background: var(--card)`, `border: 1px solid var(--border)`, `border-radius: 12-16px`, `padding: 20-24px`)
- Add a subtle accent-colored number or left border to each card to reinforce sequence
- Stagger the card animations for sequential reveal
- The heading should be a small uppercase `h3` label ("Agenda" or "What We'll Cover") with the accent color, NOT a large `h2`
- Do NOT use a plain left-aligned text list — the agenda must look as polished as any other slide

Example HTML structure:
```html
<h3 class="anim">What We'll Cover</h3>
<div class="card-grid anim stagger" style="grid-template-columns: repeat(3, 1fr);">
  <div class="card" style="text-align:left;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
      <span style="color:var(--accent);font-weight:700;font-size:clamp(1rem,1.5vw,1.5rem);">01</span>
      <span class="material-icons-round" style="color:var(--accent);font-size:clamp(1.5rem,2.5vw,2rem);">icon_name</span>
    </div>
    <h4 style="font-size:clamp(0.9rem,1.4vw,1.2rem);">Section Title</h4>
    <p style="font-size:clamp(0.75rem,1.1vw,1rem);">Brief descriptor</p>
  </div>
  <!-- repeat for each section -->
</div>
```

---

## Visual Components

Every single slide MUST have a visual component. Text-only slides are not allowed.

**Read `references/visual-components.md`** for the full catalog with HTML/CSS for each component: Card Grid, Comparison Panel, Stat Callout, Step Flow, Quote Block, Icon + Label List, Code Block, Timeline, Image + Caption, Metric Dashboard, Architecture Diagram, Progress Ring, Animated Counter, Gradient Illustration, Inline SVG Diagram, Custom Graphic, Table, Two-Column Layout, CTA Block, Callout Banner, Tag / Badge Row.

---

## HTML Output

Generate a single self-contained HTML file. No external fonts, CDN links, or images. Everything inline.

**Layout:** Fullscreen slides (100vw × 100vh), content centered, max-width `min(1200px, 92vw)`, padding `clamp(1.5rem, 4vh, 3.5rem) clamp(1.5rem, 5vw, 4rem)`. Fill the viewport — designs that leave large side margins waste screen real estate, especially on projectors and wide monitors.

**Colors:** Background `#0a0a0a`, text `#ffffff`, secondary `#a0a0a0`, cards `#1a1a1a`, borders `#2a2a2a`, plus one accent color per deck (see `references/accent-colors.md`).

**Typography:** Use relative units — no hardcoded `px` for font sizes or spacing. Reference values:
- H2 slide titles: `clamp(2.5rem, 4vw, 4rem)`
- H3 eyebrow labels: `clamp(0.85rem, 1.2vw, 1rem)`
- Body / list items: `clamp(1rem, 1.6vw, 1.5rem)`
- Stat numbers: `clamp(4rem, 7vw, 6rem)` in accent color
- Code blocks: `clamp(0.875rem, 1.2vw, 1.125rem)` monospace
- Small captions: `clamp(0.75rem, 1vw, 0.9rem)`

For spacing (padding, margin, gap) use `vh`/`vw` or `rem` instead of `px`. When setting a `px` value makes sense (e.g., icon size, border width, border-radius), keep it — but never for layout dimensions or font sizes.

**Navigation:** Arrow keys to move slides, counter in bottom-right, click-to-advance. The nav block MUST be preceded by `<div class="counter"></div>` — required by `generate_qr_appendix.py` as its insertion point. Renders as a frosted-glass pill fixed to the bottom-right with accent-colored arrow buttons and a dimmed notes hint on the right.

**Slide Transitions:** Fade crossfade using `opacity` + `pointer-events`. Never toggle `display: none / display: flex` — this breaks CSS transitions.

**Speaker Notes:** When the user requests speaker notes, store each slide's notes in a hidden `<div class="speaker-notes">` inside the slide. Two modes are available, mutually exclusive — opening one closes the other:

**Speaker notes formatting rule:** Text the presenter reads aloud appears as plain prose. Any text **not** meant to be spoken — stage directions, click cues, reminders, asides — MUST be wrapped in square brackets: `[Pause here]`, `[Click to advance]`, `[Reference the chart on the left]`. The presenter knows to skip bracketed content when speaking.
- `N` — popup window (ideal for dual-monitor setups)
- `B` — bottom panel that shrinks the slide area upward (ideal for single-monitor)

Read `references/presentation-runtime.md` for the complete nav HTML/CSS, slide transition CSS, and speaker notes CSS/HTML/JS.

**Visuals:** Use inline SVG for diagrams, flow arrows, and progress rings. Use CSS gradients (radial, linear, conic) for decorative slide backgrounds. All visual elements must be self-contained — no external images or assets. Material Icons remain the primary icon system.

**CSS Animations:** Read `references/css-animations.md` for approved patterns (fade-in, stagger, counter roll-up, progress ring, SVG draw, pulse) and rules including `prefers-reduced-motion` requirements.

---

## Content Rules

1. **One idea per slide.** If you have two points, make two slides
2. **Aim for ~30 words per slide.** Slides are visual aids, not documents. This is a guideline, not a hard limit — some slides (e.g., comparison panels, step flows) may need more.
3. **Every slide has a visual component.** No exceptions. See `references/visual-components.md`
4. **Consistent accent color.** Pick one accent and use it for all highlights, buttons, and emphasis
5. **No bullet point dumps.** If you need bullets, use an Icon + Label List component instead
6. **Big text beats small text.** When in doubt, make it bigger
7. **Use the full viewport efficiently.** Set `max-width: min(1200px, 92vw)` and use `clamp()`-based padding so content fills the available space on any screen size. Projectors and wide monitors have room — don't waste it with oversized margins. That said, keep breathing room *between* elements; the goal is balanced density, not clutter.
8. **Use Google Material Icons instead of emojis.** Load via `<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">`. Use `<span class="material-icons-round">icon_name</span>` for all icons. The endpoint must be `icon?family=` (NOT `css2?family=`), and the CSS class must be `material-icons-round` (NOT `material-icons-rounded`).
9. **Use CSS animations when they aid the presentation.** See `references/css-animations.md` for approved patterns and rules.
10. **Use CSS illustrations, SVG shapes, and gradients for visual elements.** Do not rely solely on Material Icons. All visuals must be inline — no external images. Keep total file size under 500KB.
11. **No double bullets.** When list items use a leading symbol, emoji, or icon as a visual marker, the parent `<ul>` MUST set `list-style: none; padding: 0;` to suppress the browser's default bullet.
12. **Left-align bulleted lists — or drop the bullets.** All `<ul>` and `<ol>` elements that use bullet markers MUST use `text-align: left`. When a list lives inside a centered container, explicitly set `text-align: left` on the list element.
13. **Clickable links open in a new tab with presentation-friendly styling.** All `<a>` tags MUST include `target="_blank" rel="noopener"`. Style with accent color underline: `a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--accent); transition: color 0.2s; } a:hover { color: var(--accent); }`
14. **QR code appendix slide.** When the deck contains any `<a>` links to external URLs, run `python scripts/run_script.py generate_qr_appendix.py <deck.html>` after building. The script is idempotent. QR codes MUST use black modules on a white background for reliable scanning. **A single QR appendix slide may contain a maximum of 6 QR codes.** If the deck has more than 6 external links, split them across multiple appendix slides (up to 6 QR codes per slide).
15. **Architecture and flow diagrams must be full-width and readable.** Any SVG diagram with 4+ nodes, branching paths, or multi-level structure MUST use a **full-width layout** — never place it in a two-column grid where it gets half the slide. Shrinking a complex diagram to fit alongside a bullet list makes it unreadable. Instead, use one of these layouts:
    - **Full-width diagram** (SVG spans the slide width, `width="100%"` or `width="720"`) with a compact 2-column icon list *below* the diagram.
    - **Diagram-only slide** where the architecture is the entire content with labels embedded in the SVG.
    - A two-column layout is only acceptable for **simple 2–3 node diagrams** (e.g., a single flow arrow between two boxes).
    Minimum readable sizes: node box height ≥ 36px; label `font-size` ≥ 12 (in viewBox units); connector arrow length ≥ 16px. If a diagram would need text smaller than 12px to fit in a column, it MUST be promoted to full-width.
16. **SVG layout integrity — three hard rules:**
    - **No overlapping rects.** For each column of stacked `<rect>` boxes, verify `y_N + height_N < y_(N+1)` before writing. Overlapping boxes silently clip text — the browser renders both without error. Require a minimum 10px gap between boxes.
    - **No rotated text.** `transform="rotate(...)"` on a `<text>` element almost always means the container is too narrow. Fix it by widening the container, using a multi-line label, or redesigning the output as a proper readable box.
    - **SVG `max-height` ≥ 58vh.** Diagrams with `max-height: 52vh` or lower render too small and leave large empty black bands below them on the slide. Use at least `58vh`; `65vh` is preferred for full-width architecture diagrams.
17. **When removing a stat card from a grid, update the column count.** Dropping a card from `grid-template-columns:repeat(4,1fr)` without updating the repeat value leaves remaining cards stretched across empty columns. Always update `repeat(N,1fr)` to match the actual number of cards remaining.
18. **Wrong is 3× worse than unknown — omit unconfirmed facts.** If a customer-specific figure or any `[INFERRED]` fact cannot be confirmed by the user, remove it entirely. An omission is always safer than a wrong number in a customer-facing presentation — and wrong numbers tend to appear in 5–7 places at once. When in doubt, say "we're exploring this" rather than stating an unverified figure.
19. **SVG diagram boxes must be sized to fit their text — never guess.** Size each `<rect>` width to the longest label it contains. Default to ≥ 200px for any box with a function name, SQL keyword, or long token (e.g., `SYSTEM$STREAM_HAS_DATA()`). Add at least 24px total horizontal padding. Expand the SVG `viewBox` width to match — never let a box clip its label. For single-column flow diagrams, `viewBox="0 0 260 H"` with `cx=130` is a safe default.
20. **Executive decks use BLUF structure and action titles (exec_mode).** When `exec_mode` is true:
    - Every slide `<h2>` title MUST be a **declarative assertion** — a sentence that states the conclusion — not a noun label.
      - ❌ `"Data Architecture"` → ✅ `"Snowflake Eliminates Data Silos Without Migration Risk"`
      - ❌ `"Key Benefits"` → ✅ `"Three Capabilities That Directly Reduce Your Cost Per Query"`
    - The Executive Summary slide (s2) MUST use a **CTA Block or Stat Callout** — one bold statement, one supporting line, one key metric if available. No bullet lists. No context before this slide.
    - **Cap the deck at 7 content slides.** If content does not fit, cut it — never add slides.
    - **Skip the Agenda slide entirely.** Executives prefer to reach the point immediately.

- ✋ Step 6: After presenting the deck, wait for user feedback before iterating
