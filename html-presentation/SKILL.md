---
name: html-presentation
description: "Generate beautiful self-contained HTML presentations with rich visual components. Use when: html presentation, html slides, html deck, html slide deck, self-contained presentation. Do NOT use for PowerPoint, Google Slides, or PPTX requests."
---

# HTML Presentation

## Quick Reference

| Item | Value |
|------|-------|
| Folder | `[customer-slug]/[topic-slug]/` or `[topic-slug]/` |
| HTML file | `[topic-slug]-[audience-slug]-slides.html` |
| Checkpoints | `-config.yaml`, `-brief.md`, `-plan.md`, `manifest.json` |
| Max slides | 30 (standard), 7 (exec) |
| Max words/slide | ~30 (guideline) |
| Accent color | `:root { --accent: #hex; }` — see `references/accent-colors.md` |
| Icons | Material Icons Round via `icon?family=Material+Icons+Round` |
| Transitions | Opacity + pointer-events only, never `display:none` |
| SVG min height | `max-height >= 58vh` on containers |
| Scripts | Always via `scripts/run_script.py <script.py> [args]` from the skill root (`html-presentation/`). Confirm `scripts/` exists before building. |
| Steps | 0 (resume) → 1 (gather) → Research → 1.5 (verify brief) → 2 (plan) → 3 (build) → 3.5 (shell verify) → 4 (preview) → 5 (validate) → 6 (iterate) |

---

## Shell Safety Rules

**NEVER use heredoc syntax** (`<<EOF`, `<<'EOF'`, `cat <<EOF`, etc.) or multi-line `python3 -c "..."` strings in bash. The terminal freezes while reading from `/dev/stdin` or processing complex multi-line bash patterns — this is a known Cortex Code bug that causes indefinite hangs or "Bad substitution" errors.

Instead, use the **Write tool** to create a temporary file first, then run the command against that file:
1. Use the `write` tool to save content to a `.py`, `.sh`, `.json`, or other file (in `/tmp/` or the project folder)
2. Run the command referencing that file path: `python3 /tmp/script.py`, `bash /tmp/setup.sh`, etc.

---

## Workflow

### Step 0: Resume Check

Before doing anything else, check whether a prior run was interrupted. The presentation folder follows this structure:

- **With customer**: `[customer-slug]/[topic-slug]/` (e.g., `acme/cortex-ai/`)
- **No customer**: `[topic-slug]/` (e.g., `cortex-ai/`)

**Check for `manifest.json` first.** If it exists, read it to determine the last completed step and resume from there. The manifest tracks all artifacts and their status:

```json
{
  "topic": "cortex-ai-overview",
  "customer": "acme-corp",
  "audience": "engineering-team",
  "created": "2026-04-06T10:30:00Z",
  "artifacts": {
    "config": {"path": "cortex-ai-overview-config.yaml", "status": "complete"},
    "brief": {"path": "cortex-ai-overview-brief.md", "status": "complete"},
    "plan": {"path": "cortex-ai-overview-plan.md", "status": "complete"},
    "html": {"path": "cortex-ai-overview-engineering-team-slides.html", "status": "building", "last_slide": 5}
  }
}
```

**Fallback: check for individual checkpoint files** if `manifest.json` is missing:

- `[folder]/[topic-slug]-config.yaml` — all Step 1 answers (means Step 1 is done; skip to Research or Step 2)
- `[folder]/[topic-slug]-brief.md` — research brief with sourced, tagged facts (means research is done)
- `[folder]/[topic-slug]-plan.md` — approved slide plan (means Step 2 is done; proceed directly to Step 3)
- `[folder]/[topic-slug]-[audience-slug]-slides.html` — HTML file exists. Inspect its content:
  - Contains `<!-- INSERT_SLIDE_N -->` → build is in progress; resume from slide N (skip all slides before N and continue inserting from there)
  - No such marker → build is complete; proceed to Step 5

If checkpoint files exist, read them and resume from the furthest completed step. Inform the user: "Found a prior checkpoint — resuming from Step N."

**Precedence rule:** If both `manifest.json` and `<!-- INSERT_SLIDE_N -->` markers exist in the HTML file, the HTML markers are authoritative — always prefer them over the manifest's `last_slide` value.

If no checkpoint files exist, proceed normally from Step 1.

---

### Step 1: Gather Content

Collect information from the user in **three batched rounds** (four if presenter/image details are needed). Use `ask_user_question` to present multiple questions per round rather than asking one at a time.

**Round 0 — Source material (always ask first):**

Before asking about topic or audience, explicitly ask the user what content they want to base the presentation on. Use `ask_user_question` with a multi-select:

"What source material should this presentation be based on?" Options:
- **URLs** — "I have one or more web pages (blog posts, docs, guides)"
- **Documents** — "I have files (PDF, Word, notes, transcripts)"
- **My own knowledge** — "I'll describe the topic and key points myself"
- **Existing slides** — "I have a prior deck I want to rebuild or restyle"

This question is mandatory even if the user already provided content in their initial message. If they did, acknowledge what they provided and ask: "I see you shared [URL / document / topic description]. Do you have any additional source material you'd like to include, or is this everything?"

**Processing source material:**

For each source the user provides:
- **URLs**: Fetch and store each one following the "Handling URL-based source material" rules below. If multiple URLs are provided, fetch all of them and store each as a separate `[topic-slug]-source-N.md` file (or a single combined `[topic-slug]-source-content.md` with clear section dividers).
- **Documents**: Read the file(s) using the `read` tool. Store a copy in the presentation folder. Extract topic, key points, and terminology to pre-fill Round 1 and Round 2 defaults.
- **Own knowledge**: No pre-processing needed — proceed to Round 1 and let the user describe the topic.
- **Existing slides**: Read the file (HTML, PDF, or PPTX). Extract the slide structure, content, and styling to inform the new deck plan. Store a copy in the presentation folder.

After all source material is collected and stored, proceed to Round 1 with pre-filled defaults derived from the source content (topic name, suggested key points, suggested slide count based on content depth).

**Round 1 — Core info (ask all at once):**
- **Topic** and audience
- **Customer** — is this presentation for a specific customer? If yes, ask for the customer name. Use the customer name in the title slide subtitle and personalize examples throughout the deck to reference their context.
- **Industry** — single-select: Advertising, Media & Entertainment / Financial Services / Healthcare & Life Sciences / Manufacturing / Public Sector / Retail & Consumer Goods / Technology / Telecom / Other. If "Other", ask them to specify. Use the selected industry to tailor examples, use cases, terminology, and icons throughout the deck.

**Round 2 — Configuration (ask all at once, with smart defaults):**
- **Features to include** (multi-select): Speaker notes, Presenter slide, Executive mode (BLUF-first, 7 slide cap), Custom graphics

> **Agent note:** When exec mode is selected, follow the exec deck plan in Step 2 and the action-title rules in Content Rules #20.
- **Slide count preference** — auto-suggest based on topic complexity: simple topics (overview, intro) default to 7; moderate topics (architecture, workshop) default to 12–15; deep-dive topics (technical deep-dive, hands-on, training) default to 20–25. User can override.
- **Key points** they want to cover (or offer to suggest based on topic)
- **Brand/accent color** — auto-select from `references/accent-colors.md` based on topic keywords. Present the suggested color with an option to override.
- **Title slide logo** — offer three options: (1) Snowflake logo (`assets/snowflake-logo.svg`), (2) a different logo they provide, or (3) no logo. If they choose option 2, collect the file path (or let them paste/attach the image in a follow-up message).

**Smart defaults based on topic detection:**
- **Accent color**: Match topic keywords against the `accent-colors.md` table (illustrative only — always read the file for authoritative mappings)
- **Exec mode**: If audience contains "VP", "C-suite", "board", "executive", auto-suggest exec mode ON
- **Slide count**: "overview" or "intro" → 7; "architecture" or "workshop" → 12–15; "deep-dive" or "training" → 20–25

**Round 3 — Follow-up (only if needed):**
Only ask if the user selected Presenter slide or Custom logo/graphics in Round 2:
- **Presenter details**: For each presenter: (1) full name, (2) title/role. Optionally ask if they'd like to include a headshot photo — they can provide a file path **or paste the image directly into the chat**. The presenter count determines the layout (see Presenter slide visual rules). The presenter slide does NOT count toward the slide count max. Maximum of 9 presenters.
- **Image paths**: For custom logos and graphics, collect file paths or let them paste in a follow-up message. Advise the user that images with a transparent background work best against the dark slide theme.

**Handling the title slide logo:**
- **Snowflake logo**: Note that you will place a `{{SNOWFLAKE_LOGO}}` placeholder in the HTML during Step 3 — the embed phase handles the rest. Do NOT attempt to write any SVG now.
- **Custom logo (SVG)**: Use a `{{LOGO_INLINE:path}}` placeholder (standalone token, not inside `<img>`). If sizing is needed, pass CSS as the second arg: `{{LOGO_INLINE:path|height:60px;display:block;margin:0 auto}}`. This automatically stamps `role="img"` on the SVG so `validate_deck.py` skips geometry checks (aspect ratio, viewBox gaps, etc.) that apply to diagrams but not logos. See `references/graphics-embedding.md`.
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

**Handling user-provided image file paths:** When the user provides a path to an image file, verify the file exists before copying. If it does not exist, inform the user: "I couldn't find a file at [path]. Please double-check the path or paste the image directly into the chat." If it exists, copy it into the presentation folder:
1. Copy the file to `[folder]/` (preserving the original filename)
2. Use the new `[folder]/filename` path in all subsequent references
3. Inform the user: "Copied `filename` to the presentation folder."

**Source material processing rules** (referenced by Round 0 above):

If the user provides a document, transcript, or notes, extract these elements automatically and propose defaults for each field above.

**Handling URL-based source material:** When the user provides a URL as the topic source (e.g., a blog post, documentation page, or guide):

1. **Fetch the complete content** using the `web_fetch` tool. Do NOT assume that a single fetch captures everything — check if the returned content appears truncated (e.g., the page structure ends mid-section, content is cut off, or the response metadata indicates partial content).
2. **If content is truncated**, make additional `web_fetch` calls or use `browser_snapshot` / `browser_navigate` to capture the remaining sections. Continue until the full page content is captured.
3. **Store the raw content** as `[folder]/[topic-slug]-source-content.md` immediately after fetching. This file is the authoritative reference for all content decisions — it persists across context resets so the agent never needs to re-fetch.
4. **Never assume partial content is sufficient.** If the source page has N sections (visible from headings or a table of contents), verify all N sections are present in the stored content. If any are missing, fetch again or navigate to anchor links to capture them.
5. **Add the source artifact to `manifest.json`:**
   ```json
   "source_content": {"path": "[topic-slug]-source-content.md", "source_url": "https://...", "status": "complete"}
   ```
6. **Pass the full stored content** (not a summary) to the Research Subagent prompt and to each slide-building subagent. Reference the file path so subagents can read it directly if the inline content is too large.

**After gathering topic and customer, create the presentation folder:**

- Derive `[topic-slug]` from the topic (lowercase, hyphen-separated, e.g., `cortex-ai-overview`)
- Derive `[customer-slug]` from the customer name if provided (lowercase, hyphen-separated, e.g., `acme-corp`)
- Derive `[audience-slug]` from the audience description (lowercase, hyphen-separated, max 2–3 words, e.g., `exec`, `engineering-team`, `sales-leadership`, `all-hands`)
- Create the folder: `[customer-slug]/[topic-slug]/` if a customer was given, otherwise `[topic-slug]/`
- All artifacts for this presentation (brief, plan, HTML, images) will be written to this folder
- Inform the user: "Created presentation folder: `[folder-path]`"

**⚠️ MANDATORY STOPPING POINT**: You MUST present these questions to the user and wait for their answers before proceeding. Do NOT skip ahead to planning or building. Even if the user's initial message implies a topic, you must still confirm all items (topic/audience, customer, industry, slide count, key points, accent color, speaker notes, title logo, custom graphics, presenter slide, executive audience) with the user before moving to Step 2.

**Image collection follow-up:** After the user answers the Step 1 questions, check if they indicated they want to include images (headshots, logos, screenshots, etc.) but did NOT yet provide a file path or paste an image. If any images are still outstanding, prompt the user **before** moving to Step 2:
- "You mentioned you'd like to include [a headshot / a logo / custom graphics]. Go ahead and paste or drop the image(s) here (type any text like 'here you go' along with it so you can press Enter), or provide a file path. I'll wait before moving on to the slide plan."
- Do NOT proceed to Step 2 until all referenced images have been received (as a pasted image or a file path) or the user explicitly says to skip them.

**Config checkpoint:** After all answers are collected, save a `[folder]/[topic-slug]-config.yaml` file with all gathered configuration:

```yaml
topic: "Cortex AI Overview"
audience: "Engineering Team"
customer: "Acme Corp"
industry: "Technology"
slide_count: 10
key_points:
  - "Real-time AI inference"
  - "Cost optimization"
accent_color: "#29B5E8"
speaker_notes: true
logo: "snowflake"
exec_mode: false
presenter:
  - name: "Jane Doe"
    title: "Solutions Architect"
    photo: "acme/cortex-ai/pasted_headshot_1711700000.png"
sources:
  - type: "url"
    path: "cortex-ai-overview-source-content.md"
    original: "https://www.snowflake.com/en/developers/guides/..."
custom_graphics: []
```

Also create or update `[folder]/manifest.json` with the config artifact status set to `"complete"`. This ensures that if context resets during any later step, the agent can resume from config without re-asking all questions.

---

### Research Subagent

Before proceeding to Step 2, always ask the user whether they'd like to run a research subagent to gather supporting facts, statistics, and examples for the deck. Ask even if the user has already provided their own notes, document, or transcript — research can supplement user-provided content with additional data points.

Use `ask_user_question` to present the choice: "Would you like me to research your topic to gather supporting statistics, examples, and quotes? This typically takes 1–2 minutes." Options: (1) Yes — run research, (2) No — skip and use only the content I've provided.

If the user selects **Yes**, launch a `general-purpose` subagent **before** Step 2 to build a factual brief. If the user provided their own content, include it in the subagent prompt as additional context alongside the research instructions.

**Before launching**, inform the user: "Researching your topic — this may take a minute or two."

**Subagent type:** `general-purpose` | **readonly:** `true`

Prompt: Read `references/research-prompt.md` and use its full contents as the subagent prompt, substituting `[TOPIC]`, `[AUDIENCE]`, `[KEY_POINTS]`, and `[EXEC_MODE]` with the current values.

Use the returned brief as the factual foundation for slide copy in Step 2.

**⚠️ Accuracy calibration — wrong is 3× worse than unknown:** Before using any fact from the brief in slide copy, check its tag:
- `[EXTRACTED]` facts may be used directly; cite the source in speaker notes.
- `[INFERRED]` facts must be presented to the user for confirmation before being written into slide copy.
- `[UNVERIFIED — confirm with customer]` facts MUST be confirmed by the user during Step 1.5 before being placed in the deck. A wrong stat is costly to fix because it typically appears in multiple places: stat cards, SVG `<text>` labels, speaker notes, tooltips, and bullet lists. **If a fact cannot be confirmed, omit it — never use the researched estimate.**

**Checkpoint:** Save the full brief (with all tags and citations intact) to `[folder]/[topic-slug]-brief.md` immediately after the subagent returns. This file is a citable research artifact — do not strip or summarize the tags and sources when saving. Update `manifest.json` with the brief artifact status.

**URL validation (mandatory after saving brief):** Extract every URL from the brief and verify it resolves. This script accepts any text file (markdown or HTML) and checks all URLs it contains. Run:
```bash
python scripts/run_script.py validate_urls.py [folder]/[topic-slug]-brief.md
```
For any URL that returns a non-200 status or times out:
1. Mark it `[DEAD LINK]` inline in the brief file
2. Do NOT use it as a citation in slide copy or speaker notes
3. If the source is the only citation for a key fact, downgrade that fact from `[EXTRACTED]` to `[INFERRED]` and note the dead link

This validation runs on the brief — the HTML link validation in Step 3 is a separate check on links written into the deck itself.

**Bot-detection fallback:** If `validate_urls.py` reports `403-bot-blocked` for any URL, use the `web_fetch` tool to validate those URLs individually. If `web_fetch` returns content successfully, the URL is valid — ignore the 403. If `web_fetch` also fails, the URL is genuinely broken.

---

### Step 1.5: Verify Research Brief

**Skip this step if the user chose not to run the Research Subagent.** Proceed directly to Step 2.

**⚠️ MANDATORY STOPPING POINT**: After the research subagent returns and the brief is saved, present the research brief to the user. Highlight:

- `[EXTRACTED]` facts — these may be used directly; cite the source in speaker notes. Present them for awareness but confirmation is not required.
- All facts tagged `[INFERRED]` — ask the user to confirm or reject each one
- All facts tagged `[UNVERIFIED — confirm with customer]` — these MUST be confirmed or removed before any are placed in the deck. A wrong stat is costly to fix because it typically appears in multiple places: stat cards, SVG `<text>` labels, speaker notes, tooltips, and bullet lists.
- Any dead links found by `validate_urls.py` — note which facts lost their citation
- The suggested narrative arc — confirm this matches the user's intent. If the user rejects it, update the brief with the corrected structure before saving.

Do NOT proceed to Step 2 until the user has reviewed and approved the brief. Apply any user corrections (rejected facts, updated numbers, alternative sources) and save the corrected brief back to `[folder]/[topic-slug]-brief.md`.

If the user rejects a fact or cannot confirm it, remove it entirely — never leave an unconfirmed fact in the brief as a temptation for later slide copy. **If a fact cannot be confirmed, omit it — never use the researched estimate.**

---

### Step 2: Plan the Slide Deck

Map each slide to a visual component (see `references/visual-components.md`). Present the plan:

```
Slide 1: Title -- "Topic Name" with subtitle + accent gradient
Presenter: [if requested] Name, title, and optional headshot for each presenter (does not count toward slide max)
Agenda: Icon + Label List of thematic sections (does not count toward slide max)
BLUF: Bottom Line Up Front — 2–4 card summary of the key takeaways (does not count toward slide max)
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

**Checkpoint:** Once the user approves, save the full slide plan to `[folder]/[topic-slug]-plan.md` before starting the build. Update `manifest.json`.

---

## Slide Structure

> **Reference section** — read before Step 3, not a step itself.

Every deck follows this proven flow:

| Slide | Purpose | Content |
|-------|---------|---------|
| **1. Title** | Set the stage | Big title, subtitle, your name or brand |
| **Agenda** | Orient the audience | Numbered card grid of 3–6 thematic sections (not counted toward slide max) |
| **BLUF** | Bottom Line Up Front | 3-card summary stating the key takeaways upfront (not counted toward slide max) |
| **2. Setup** | Frame the problem or context | Why this matters, what the audience will learn |
| **3-8. Core Content** | Deliver the meat | One idea per slide, each with a visual component |
| **9. Evidence** | Prove your point | Stats, quotes, case studies, examples |
| **10. Takeaway** | Land the message | Summary, call to action, next steps |

Adjust the number of core content slides based on topic complexity. Simple topics: 5–7 total slides. Moderate topics: 10–15 slides. Deep-dive topics: 20–25 slides. Never exceed 30 slides.

**Executive Deck Structure (exec_mode):** When `exec_mode` is true, follow the executive deck plan in Step 2 (BLUF-first, 7-slide cap, no Agenda slide). Cap at **7 content slides**.

**Presenter Slide (optional):** If the user requests a presenter slide, include it immediately after the Title slide (before the Agenda). The Presenter slide does NOT count toward the slide count max.

**Presenter slide visual rules:** See the **Presenter Slide** section in `references/visual-components.md` for exact layout, headshot sizing, and CSS values for 1, 2, and 3+ presenter layouts. All presenter headshots MUST be circularly cropped (`border-radius: 50%; object-fit: cover; equal width/height`). Maximum of 9 presenters — `insert_presenter.py` will error if this limit is exceeded.

For HTML patterns, see the **Presenter Slide** section in `references/visual-components.md`.

**Agenda Slide (mandatory, except exec decks):** Every non-exec deck MUST include an Agenda slide immediately after the Title slide (or after the Presenter slide, if present). Exec decks skip the Agenda entirely — see exec_mode rules. The Agenda does NOT count toward the slide count max. List 3-6 thematic sections (not every individual slide).

**BLUF Slide (mandatory for non-exec decks):** Every non-exec deck MUST include a BLUF (Bottom Line Up Front) slide immediately after the Agenda slide. The BLUF does NOT count toward the slide count max. In exec mode, there is no standalone BLUF slide — the BLUF content is embedded directly in Slide 2 (Executive Summary). Use a card layout (2–4 cards) where each card states one key takeaway the audience will leave with — written as a concrete outcome, not a topic label. Keep each card to a headline (bold, white) + 1–2 sentence elaboration (secondary color). Use a relevant Material Icon per card (accent-colored). The eyebrow `h3` should be a short, contextually appropriate label.

**Agenda visual rules:**
- Use a **numbered grid of cards** (2 or 3 columns), one card per section
- Each card gets: a Material Icon (accent-colored, `clamp(1.5rem, 2.5vw, 2rem)`), a bold section title (`clamp(0.9rem, 1.4vw, 1.2rem)` white), and a one-line descriptor (`clamp(0.75rem, 1.1vw, 1rem)` secondary color)
- Cards use the standard card style (`background: var(--card)`, `border: 1px solid var(--border)`, `border-radius: 12-16px`, `padding: 20-24px`)
- Add a subtle accent-colored number or left border to each card to reinforce sequence
- Stagger the card animations for sequential reveal
- The heading should be a small uppercase `h3` label (e.g., "Agenda", "What We'll Cover", "Today's Session") with the accent color, NOT a large `h2`
- Prefer a card grid over a plain text list — it looks more polished and consistent with the rest of the deck. A simple icon list is acceptable for short agendas (3 items or fewer) where a card grid would feel heavy.

For the full HTML pattern, see the **Agenda** section in `references/visual-components.md`.

---

## Content Rules

> **Reference section** — read before Step 3, not a step itself.

1. **One idea per slide.** If you have two points, make two slides
2. **Aim for ~30 words per slide.** Slides are visual aids, not documents. This is a guideline, not a hard limit — some slides (e.g., comparison panels, step flows) may need more.
3. **Every slide has a visual component.** No exceptions. Card Grids, Icon+Label Lists, Stat Callouts, CTA Blocks, and all other components from the catalog qualify. A slide with only an `<h2>` title and `<p>` body text — no component — is not allowed. See `references/visual-components.md`
4. **Consistent accent color.** Pick one accent and use it for all highlights, buttons, and emphasis
5. **No bullet point dumps.** If you need bullets, use an Icon + Label List component instead
6. **Big text beats small text.** When in doubt, make it bigger
7. **Use the full viewport efficiently.** Set `max-width: min(1200px, 92vw)` and use `clamp()`-based padding so content fills the available space on any screen size. Projectors and wide monitors have room — don't waste it with oversized margins. That said, keep breathing room *between* elements; the goal is balanced density, not clutter.
8. **Use Google Material Icons instead of emojis.** Load via `<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">`. Use `<span class="material-icons-round">icon_name</span>` for all icons. The endpoint must be `icon?family=` (NOT `css2?family=`), and the CSS class must be `material-icons-round` (NOT `material-icons-rounded`).
9. **Use CSS animations when they aid the presentation.** Use entrance animations (fade-in, stagger) on every slide's primary content. Avoid looping animations on static reference slides. Always respect `prefers-reduced-motion`. See `references/css-animations.md` for approved patterns and rules.
10. **Use CSS illustrations, SVG shapes, and gradients for visual elements.** Do not rely solely on Material Icons. All image visuals must be inline — no external image assets (the Material Icons CDN link is the only permitted external dependency). Aim to keep total file size under 2MB. For decks with no embedded images, under 500KB is ideal. When images are embedded via `embed_image.py`, exceeding 500KB is acceptable.
11. **No double bullets.** When list items use a leading symbol, emoji, or icon as a visual marker, the parent `<ul>` MUST set `list-style: none; padding: 0;` to suppress the browser's default bullet.
12. **Left-align bulleted lists — or drop the bullets.** All `<ul>` and `<ol>` elements that use bullet markers MUST use `text-align: left`. When a list lives inside a centered container, explicitly set `text-align: left` on the list element.
13. **Clickable links open in a new tab with presentation-friendly styling.** All `<a>` tags MUST include `target="_blank" rel="noopener"`. Style with accent color underline: `a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--accent); transition: color 0.2s; } a:hover { color: var(--accent); }`
14. **QR code appendix slide.** When the deck contains any `<a>` links to external URLs, run `python scripts/run_script.py generate_qr_appendix.py <deck.html>` after building. The script is idempotent. QR codes MUST use black modules on a white background for reliable scanning. **A single QR appendix slide may contain a maximum of 6 QR codes.** If the deck has more than 6 external links, split them across multiple appendix slides (up to 6 QR codes per slide). (This rule is enforced automatically by `generate_qr_appendix.py` — slide authors do not need to track the total link count.)
15. **Architecture and flow diagrams must be full-width and readable.** Any SVG diagram with 4+ nodes, branching paths, or multi-level structure MUST use a **full-width layout** — never place it in a two-column grid where it gets half the slide. Shrinking a complex diagram to fit alongside a bullet list makes it unreadable. Instead, use one of these layouts:
    - **Full-width diagram** (SVG spans the slide width, `width="100%"` or `width="720"`) with a compact 2-column icon list *below* the diagram.
    - **Diagram-only slide** where the architecture is the entire content with labels embedded in the SVG.
    - A two-column layout is only acceptable for simple, linear diagrams where each element remains clearly readable at half-slide width.
    Minimum readable sizes: node box height >= 36px; label `font-size` >= 12 (in viewBox units); connector arrow length >= 16px. If a diagram would need text smaller than 12px to fit in a column, it MUST be promoted to full-width.
16. **SVG layout integrity — five hard rules:**
    - **No overlapping rects.** For each column of stacked `<rect>` boxes, verify `y_N + height_N < y_(N+1)` before writing. Overlapping boxes silently clip text — the browser renders both without error. Require a minimum 10px gap between boxes.
    - **No rotated text.** `transform="rotate(...)"` on a `<text>` element almost always means the container is too narrow. Fix it by widening the container, using a multi-line label, or redesigning the output as a proper readable box.
    - **SVG `max-height` >= 58vh.** Diagrams with `max-height: 52vh` or lower render too small and leave large empty black bands below them on the slide. Use at least `58vh`; `65vh` is preferred for full-width architecture diagrams.
    - **viewBox height must contain all content with 20px to spare.** Before writing, identify the lowest element in the diagram and compute `y + height`. The viewBox height MUST be at least that value plus 20px. Never set the viewBox height equal to the last element's bottom edge — even a 1px overrun clips silently and produces no error.
    - **Use `svg_calc.py` before writing any SVG with stacked boxes or multi-column layout.** Do not do coordinate math in your head — run the calculator first, then paste the exact values into the SVG. Commands: `stack` (y positions for stacked rects), `textbox` (minimum rect width for a label), `distribute` (cx values for N columns), `viewbox` (required viewBox height), `arrow` (connector line path), `grid` (full x/y table for multi-column rows), `layout` (complete flow diagram from JSON). Example: `python scripts/run_script.py svg_calc.py stack --count 4 --box-height 48 --gap 16`
17. **When removing a stat card from a grid, update the column count.** Dropping a card from `grid-template-columns:repeat(4,1fr)` without updating the repeat value leaves remaining cards stretched across empty columns. Always update `repeat(N,1fr)` to match the actual number of cards remaining.
18. **Wrong is 3x worse than unknown — omit unconfirmed facts.** If a customer-specific figure or any `[INFERRED]` fact cannot be confirmed by the user, remove it entirely. An omission is always safer than a wrong number in a customer-facing presentation — and wrong numbers tend to appear in 5–7 places at once. When in doubt, say "we're exploring this" rather than stating an unverified figure.
19. **SVG diagram boxes must be sized to fit their text — never guess.** Run `python scripts/run_script.py svg_calc.py textbox --text "your label" --font-size 12` to get the exact minimum box width before writing any `<rect>`. Default to >= 200px for any box with a function name, SQL keyword, or long token (e.g., `SYSTEM$STREAM_HAS_DATA()`). Add at least 24px total horizontal padding. Expand the SVG `viewBox` width to match — never let a box clip its label. For single-column flow diagrams, `viewBox="0 0 260 H"` with `cx=130` is a safe default.
20. **Executive decks use BLUF structure and action titles (exec_mode).** When `exec_mode` is true:
    - Every slide `<h2>` title MUST be a **declarative assertion** — a sentence that states the conclusion — not a noun label.
      - BAD: `"Data Architecture"` → GOOD: `"Snowflake Eliminates Data Silos Without Migration Risk"`
      - BAD: `"Key Benefits"` → GOOD: `"Three Capabilities That Directly Reduce Your Cost Per Query"`
    - The Executive Summary slide (s2) should use a high-impact component — a CTA Block, Stat Callout, or similar — with one bold statement, one supporting line, and a key metric if available. No bullet lists. No context before this slide.
    - **Cap the deck at 7 content slides.** If content does not fit, cut it — never add slides.
    - **Skip the Agenda slide entirely.** Executives prefer to reach the point immediately.

---

## HTML Output

> **Reference section** — read before Step 3, not a step itself.

Generate a single self-contained HTML file. No external images or base64-encoded assets inline. One external CDN link is permitted: Material Icons Round (`fonts.googleapis.com/icon?family=Material+Icons+Round`). All other assets must be self-contained.

**Layout:** Fullscreen slides (100vw x 100vh), content centered, max-width `min(1320px, 95vw)`, padding `clamp(1.65rem, 4.4vh, 3.85rem) clamp(1.65rem, 5.5vw, 4.4rem)`. Fill the viewport — designs that leave large side margins waste screen real estate, especially on projectors and wide monitors.

**Colors:** Background `#0a0a0a`, text `#ffffff`, secondary `#a0a0a0`, cards `#1a1a1a`, borders `#2a2a2a`, plus one accent color per deck (see `references/accent-colors.md`).

**Typography:** Use relative units — no hardcoded `px` for font sizes or spacing. Reference values:
- H2 slide titles: `clamp(2.75rem, 4.4vw, 4.4rem)`
- H3 eyebrow labels: `clamp(0.935rem, 1.32vw, 1.1rem)`
- Body / list items: `clamp(1.1rem, 1.76vw, 1.65rem)`
- Stat numbers: `clamp(4.4rem, 7.7vw, 6.6rem)` in accent color
- Code blocks: `clamp(0.96rem, 1.32vw, 1.24rem)` monospace
- Small captions: `clamp(0.825rem, 1.1vw, 0.99rem)`

For spacing (padding, margin, gap) use `vh`/`vw` or `rem` instead of `px`. When setting a `px` value makes sense (e.g., icon size, border width, border-radius), keep it — but never for layout dimensions or font sizes.

**Navigation:** Arrow keys to move slides, counter in bottom-right, click-to-advance. The nav block MUST be preceded by `<div class="counter"></div>` — required by `generate_qr_appendix.py` as its insertion point. Renders as a frosted-glass pill fixed to the bottom-right with accent-colored arrow buttons and a dimmed notes hint on the right. The JS initialization block MUST include `document.getElementById('total').textContent = slides.length;` immediately before `show(0)` — this self-corrects the counter at runtime if slides are added or removed after the initial build.

**Slide Transitions:** Fade crossfade using `opacity` + `pointer-events`. Never toggle `display: none / display: flex` — this breaks CSS transitions.

**Speaker Notes:** When the user requests speaker notes, store each slide's notes in a hidden `<div class="speaker-notes">` inside the slide. Two modes are available, mutually exclusive — opening one closes the other:

**Speaker notes formatting rule:** Text the presenter reads aloud appears as plain prose. Any text **not** meant to be spoken — stage directions, click cues, reminders, asides — MUST be wrapped in square brackets: `[Pause here]`, `[Click to advance]`, `[Reference the chart on the left]`. The presenter knows to skip bracketed content when speaking.
- `N` — popup window (ideal for dual-monitor setups)
- `B` — bottom panel that shrinks the slide area upward (ideal for single-monitor)

Read `references/presentation-runtime.md` for the complete nav HTML/CSS, slide transition CSS, and speaker notes CSS/HTML/JS.

**Visuals:** Use inline SVG for diagrams, flow arrows, and progress rings. Use CSS gradients (radial, linear, conic) for decorative slide backgrounds. All visual elements must be self-contained — no external images or assets. Material Icons remain the primary icon system.

**CSS Animations:** Read `references/css-animations.md` for approved patterns (fade-in, stagger, counter roll-up, progress ring, SVG draw, pulse) and rules including `prefers-reduced-motion` requirements.

---

## Visual Components

> **Reference section** — read before Step 3, not a step itself.

Every single slide MUST have a visual component. Text-only slides are not allowed.

**Read `references/visual-components.md`** for the full catalog with HTML/CSS for each component: Card Grid, Comparison Panel, Stat Callout, Step Flow, Quote Block, Icon + Label List, Code Block, Timeline, Image + Caption, Metric Dashboard, Architecture Diagram, Progress Ring, Animated Counter, Gradient Illustration, Inline SVG Diagram, Custom Graphic, Table, Two-Column Layout, CTA Block, Callout Banner, Tag / Badge Row, Vertical Bar Chart, Horizontal Bar Chart, Line / Area Chart, Donut Chart.

---

### Step 3: Build the HTML

Generate a single self-contained HTML file following the Slide Structure, HTML Output, and Content Rules sections above. Every slide MUST have a visual component from `references/visual-components.md`.

**Before starting**, inform the user: "Building your slide deck — this may take a few minutes while I read the reference files and generate all the slides."

**Before writing any HTML, read ALL FIVE reference files.** This is mandatory — skipping any file will cause structural errors that require significant rework:
- `references/presentation-runtime.md` — **READ THIS FIRST** — defines the exact nav HTML/CSS, slide transition CSS (opacity-only, no transform), and the complete dual-mode speaker notes system (N = popup window, B = bottom panel). Copy these patterns exactly. Do not improvise.
- `references/visual-components.md`
- `references/css-animations.md`
- `references/accent-colors.md`
- `references/graphics-embedding.md`

**Build mode:** All HTML generation — shell and slides — is delegated to subagents. The main context orchestrates: it reads reference files, launches subagents, checks progress between batches, and handles the embed/QR/validation phases. This keeps all HTML out of the main context, preserving room for iteration and error recovery.

**Inlining the Snowflake logo (if selected in Step 1):** Place a bare `{{SNOWFLAKE_LOGO}}` token on its own line as the **first child inside `.slide-inner`** on the title slide (before the `<h3>` eyebrow). The `embed_image.py` embed phase will replace it with the correct inline `<svg>` block automatically — do NOT read any SVG file, do NOT write any `<svg>` or `<path>` markup manually.

**Shell-First, Slide-by-Slide Build (required for all decks):**

Always build the deck in three phases: shell → batched slide insertion → embed. The file is saved after every single slide — the worst-case of any interruption is losing one slide in progress.

#### Phase 1 — Generate the shell (script):

Run `generate_shell.py` via `run_script.py`. This is a deterministic script — no subagent, no LLM tokens, completes in under a second. Read the slide count and settings from the approved plan and config before running.

```bash
python scripts/run_script.py generate_shell.py \
  --title "[Deck Title]" \
  --accent "[accent_color from config]" \
  --slides [N] \
  --output [folder]/[topic-slug]-[audience-slug]-slides.html \
  [--no-notes]   # omit if speaker_notes: true in config
```

The script:
- Reads `templates/shell_template.html` as its source
- Substitutes `{{TITLE}}`, `{{ACCENT}}`, `{{SLIDE_COUNT}}`
- Strips or keeps the speaker-notes CSS/HTML/JS blocks based on `--no-notes`
- Runs 4 built-in checks (INSERT_SLIDE_1 marker, total counter, counter div, accent color) and exits non-zero on any failure
- Prints: `Shell saved to [path]. Total slide count: N.`

If the script exits non-zero, read the error output and fix the arguments — do NOT fall back to a subagent. Common errors: wrong output path, missing `--accent` value, slide count mismatch.

After the script succeeds, update `manifest.json` with `html: {status: "shell_complete", "last_slide": 0}`. Then inform the user: "Shell saved — building slides now."

### Step 3.5: Shell Verification

After `generate_shell.py` succeeds, the 4 built-in checks have already passed. Do a quick confirmation in the main context before proceeding to Phase 2:

1. Confirm the output file exists at the expected path
2. Confirm the script's printed slide count matches the approved plan

If either check fails, re-run the script with corrected arguments. If both pass, proceed immediately to Phase 2.

#### Phase 2 — One subagent per slide (Step 3, continued):

Each slide is built by its own subagent. This gives every slide — especially those with complex SVG diagrams, multi-column layouts, or architecture graphics — the full context window it needs. The main context orchestrates: launch, verify, repeat.

**For each slide N in the approved plan:**

1. **Launch a slide subagent:**

   **Subagent type:** `general-purpose` | **readonly:** `false`

   Before launching the first slide, read all 5 reference files with the `read` tool in the main context. Embed all 5 reference file contents directly in each subagent prompt. Do not rely on subagents to read files independently. If the combined content is too large for a single prompt, abbreviate `css-animations.md` and `accent-colors.md` to their first 50 lines as summaries — `presentation-runtime.md` and `visual-components.md` are the most critical per-slide.

   The subagent prompt must include:
   - The slide plan entry for THIS SLIDE ONLY (e.g., "Slide 5: Core — Architecture Diagram showing the data flow")
   - The full slide plan for narrative context (so the subagent understands what comes before and after)
   - All 5 reference file contents inline (or abbreviated as described above)
   - The relevant SKILL.md sections inline: Slide Structure (Presenter, Agenda, BLUF rules), Content Rules, and HTML Output spec — required for any subagent building structural slides
   - The HTML file path
   - The working directory path (the skill root where `scripts/` is located) — for running `svg_calc.py` and other scripts via bash
   - The config (from `-config.yaml`): `accent_color` (for `--accent` CSS variable), `speaker_notes` (whether to include `<div class="speaker-notes">`), `exec_mode` (action titles vs noun labels), `customer` (personalization references), `industry` (icon and example selection)
   - Instructions to use the `edit` tool to replace `<!-- INSERT_SLIDE_N -->` with the slide HTML plus the next marker. The `old_string` must exactly match the marker text (e.g., `<!-- INSERT_SLIDE_3 -->`). The `new_string` is the slide div HTML plus the next marker:
     ```html
     <div id="sN" class="slide">
       ...slide content...
     </div>
     <!-- INSERT_SLIDE_(N+1) -->
     ```
   - For the **final slide** of the entire deck, omit the next marker — the file is complete when no `<!-- INSERT_SLIDE_ -->` markers remain

   The subagent returns: "Built slide N: [slide title]. Next marker: INSERT_SLIDE_(N+1)" (or "No remaining markers" for the final slide).

2. **Verify (main context):**

   After each subagent returns:
   - Search the HTML file for the next expected `<!-- INSERT_SLIDE_(N+1) -->` marker (or confirm no markers remain for the final slide)
   - If the marker is in the correct position, the slide succeeded — proceed to the next slide
   - If the subagent failed, relaunch it for the same slide. After 2 failed attempts, build the slide in the main context as a fallback.

3. **Update `manifest.json`** after each slide with `html: {status: "building", "last_slide": N}`. After the final slide, set `html: {status: "complete", "last_slide": N}`.

4. **Report progress to the user** after each successful slide: output a short message such as `Slide N/[total]: [slide title]`. For the final slide output: `All [total] slides complete.`

**Resuming after interruption:**

If the HTML file already exists when Phase 2 starts, search for `<!-- INSERT_SLIDE_N -->` to find the resume point. Skip all completed slides and continue from slide N. Inform the user: "Resuming from slide N."

**Post-build processing (when the deck includes user-provided images, SVGs, or the Snowflake logo):**
1. **Embed phase** — Write the HTML with placeholder tokens during Phase 1 and Phase 2. Do NOT write any `<svg>`/`<path>` markup or base64 strings during those phases.
   - `{{SNOWFLAKE_LOGO}}` — standalone token for the Snowflake logo on the title slide
   - `{{SVG_INLINE:path}}` or `{{SVG_INLINE:path|css-style}}` — standalone token for diagram/chart SVG files
   - `{{LOGO_INLINE:path}}` or `{{LOGO_INLINE:path|css-style}}` — standalone token for logo/decorative SVG files (skips geometry validation)
   - `{{IMG:path}}` or `{{IMG:path|max-px}}` — inside `<img src="...">` for raster images (PNG/JPG/etc.)
   After all slides are built, inform the user: "Embedding images — this may take a moment." Then run `python scripts/run_script.py embed_image.py <deck.html>` to resolve all tokens. This happens entirely in Python — no SVG markup or base64 data ever enters the conversation context.
2. **QR appendix phase** — If the deck contains any `<a>` links to external URLs, inform the user: "Generating QR code appendix." Then run `python scripts/run_script.py generate_qr_appendix.py <deck.html>` to scan for links and append a QR code appendix slide with inline SVG QR codes. The script auto-numbers the new slide and updates the total counter. **The script requires a `<div class="counter"></div>` marker in the HTML** to know where to insert the new slide — this MUST be included in the initial HTML build (see HTML Output > Navigation).

If the deck has no user-provided images, no SVGs, and no Snowflake logo (only Material Icons, inline CSS graphics), skip the embed phase — the HTML is already self-contained.

**3. URL validation phase** — After the QR appendix is generated, verify that every external link in the deck resolves successfully. This script accepts any text file (markdown or HTML) and checks all URLs it contains. Run:
```bash
python scripts/run_script.py validate_urls.py [folder]/[topic-slug]-[audience-slug]-slides.html
```
Any URL returning a non-200 status MUST be replaced with a live equivalent before proceeding. After fixing any broken URLs, re-run `generate_qr_appendix.py` — it is idempotent and will rebuild QR codes to encode the corrected links. Do not proceed to Step 4 with unresolved broken links.

**Bot-detection fallback:** If `validate_urls.py` reports `403-bot-blocked` for any URL, use the `web_fetch` tool to verify those URLs individually. If `web_fetch` returns content, the URL is valid. Only replace URLs that fail both methods.

For all image/graphics technical details, see `references/graphics-embedding.md`.

**Slide ID and numbering rules:**
- Every slide (including Agenda and Presenter) MUST have a sequential `id="sN"` attribute starting from `s1` for the title slide.
- The Agenda slide and Presenter slide are real slides in the HTML with their own IDs, even though they don't count toward the content slide plan.
- The `<span id="total">` counter in the navigation MUST equal the actual number of slide divs in the HTML. **Additionally**, the JS initialization MUST include `document.getElementById('total').textContent = slides.length;` before `show(0)` — this self-corrects at runtime and is enforced by `validate_deck.py` Check #2.
- When adding or removing slides after initial generation, ALL subsequent slide IDs must be renumbered to stay sequential and the total must be updated. **Always renumber in reverse order** (highest ID first, working down) to avoid double-replacement bugs. Use `scripts/insert_presenter.py` via `run_script.py` to automate post-build presenter slide injection (it handles resize, base64, insertion, renumbering, and total update in one step).

---

### Step 4: Save and Preview

Save the file as `[folder]/[topic-slug]-[audience-slug]-slides.html`. Update `manifest.json` with the html artifact status set to `"complete"`.

Open in the default browser:
```bash
open [folder]/[topic-slug]-[audience-slug]-slides.html
```

If `open` fails, try `xdg-open` (Linux) or provide the file path for manual opening.

---

### Step 5: Verify

**Validation Subagent:**

Inform the user: "Validating the deck — this may take a minute." Then delegate the automated validation and fix cycle to a subagent — this keeps error output and large HTML reads out of the main context.

**Subagent type:** `general-purpose` | **readonly:** `false`

Prompt: Read `references/validation-prompt.md` and use its full contents as the subagent prompt, substituting `[folder]`, `[topic-slug]`, `[audience-slug]`, and `[skill-root]` with the current values.

**Visual QA (after validator passes):**

Open the deck in the browser (`open [deck.html]`) and use `browser_take_screenshot` to capture key slides for visual inspection. If the screenshot tool is not available or cannot capture a local `file://` URL, note this limitation and ask the user to visually confirm the slides instead.

Capture (best-effort):
1. **Title slide** — check logo rendering, gradient background, text hierarchy
2. **One representative content slide** (preferably one with an SVG diagram or card grid) — check visual component rendering, spacing, accent color
3. **Last content slide** — check CTA/takeaway rendering
4. **QR appendix** (if present) — check QR codes are scannable (black on white)

If screenshots are captured, save them to `[folder]/screenshots/` for the user to review (create the directory if needed). If saving is not possible, present the screenshots inline in the conversation.

Then manually verify:
- Accent color is consistent across all slides
- Material Icons render correctly (not showing as text)
- Animations fire on slide enter
- Navigation works (arrow keys, slide counter visible)
- **All external links return HTTP 200** — re-run the URL validation phase if this was skipped or if any links were added during iteration
- **SVG diagrams (check each slide with an inline SVG):**
  - No two `<rect>` elements in the same column overlap — confirm `y + height` of each box is less than `y` of the next
  - No `<text transform="rotate(` present — rotated text signals a layout problem
  - `max-height` on SVG containers is >= 58vh — lower values cause excess empty slide space
  - No unverified customer facts in `<text>` elements — SVG text is easy to overlook during review. Grep for numbers and proper nouns inside `<text>` tags and confirm they match user-verified data

If any check fails, fix the HTML and re-preview before proceeding.

---

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
