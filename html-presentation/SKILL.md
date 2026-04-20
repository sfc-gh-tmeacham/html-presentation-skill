---
name: html-presentation
description: "Generate beautiful self-contained HTML presentations with rich visual components. Use when: html presentation, html slides, html deck, html slide deck, self-contained presentation. Do NOT use for: exporting PowerPoint, converting existing files to PPTX, or any non-HTML presentation task."
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
| Icons | Material Symbols Rounded via `css2?family=Material+Symbols+Rounded` |
| Transitions | Opacity + pointer-events only, never `display:none` |
| SVG min height | `max-height >= 58vh` on containers |
| Scripts | Always via `scripts/run_script.py <script.py> [args]` from the skill root (`html-presentation/`). Confirm `scripts/` exists before building. |
| PPTX export | `scripts/run_script.py export_to_pptx.py <deck.html>` — see `references/export-to-pptx.md` |
| Steps | 0 (resume) → 1 (gather) → Research → 1.5 (verify brief) → 2 (plan) → 3 (build) → 3.5 (shell verify) → 4 (preview) → 5 (validate) → 6 (iterate) → 7 (export, optional) |

**Skip Map — sections you can skip based on config:**

| Feature | Skip condition | Sections to skip |
|---------|---------------|-----------------|
| Exec mode | `exec_mode: false` | Step 2 exec deck plan, Content Rule #20 |
| Research subagent | User selects "No" to research | Research Subagent section, Step 1.5 |
| Presenter slide | Not requested in Round 2 | Round 3 (presenter details) |
| Speaker notes | `speaker_notes: false` | Speaker notes HTML/CSS/JS block in HTML Output |
| PowerPoint export | Not requested by user | Step 7 entirely |
| Post-build embed | No `{{...}}` placeholder tokens in HTML | Embed phase in Step 3 |
| QR appendix | No `<a>` links to external URLs | QR appendix phase in Step 3, Content Rule #14 |
| SVG rules | No inline SVG planned | Content Rules #15–19 |
| Architecture diagrams | No architecture/flow diagram slides | Content Rule #15 |

---

## Shell Safety Rules

**NEVER use heredoc syntax** (`<<EOF`, `<<'EOF'`, `cat <<EOF`, etc.) or multi-line `python3 -c "..."` in bash. Terminal freezes reading from `/dev/stdin` — known Cortex Code bug, causes hangs or "Bad substitution" errors.

Use **Write tool** to create temp file first, then run command:
1. Use `write` tool to save content to `.py`, `.sh`, `.json`, or other file (in `/tmp/` or project folder)
2. Run command referencing that file path: `python3 /tmp/script.py`, `bash /tmp/setup.sh`, etc.

**These rules apply to ALL subagents.** Any subagent running bash MUST receive these rules in its prompt — subagents don't inherit from SKILL.md.

---

## Workflow

### Step 0: Resume Check

Check for interrupted prior run. Presentation folder structure:

- **With customer**: `[customer-slug]/[topic-slug]/` (e.g., `acme/cortex-ai/`)
- **No customer**: `[topic-slug]/` (e.g., `cortex-ai/`)

**Check `manifest.json` first.** If exists, read to find last completed step and resume. Manifest tracks all artifacts and status:

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

**Fallback: check checkpoint files** if `manifest.json` missing:

- `[folder]/[topic-slug]-config.yaml` — Step 1 answers (Step 1 done; skip to Research or Step 2)
- `[folder]/[topic-slug]-brief.md` — research brief with sourced, tagged facts (research done)
- `[folder]/[topic-slug]-plan.md` — approved slide plan (Step 2 done; proceed to Step 3)
- `[folder]/[topic-slug]-[audience-slug]-slides.html` — HTML exists. Inspect content:
  - Contains `<!-- INSERT_SLIDE_N -->` → build in progress; resume from slide N
  - No such marker → build complete; proceed to Step 5

If checkpoint files exist, resume from furthest completed step. Inform user: "Found a prior checkpoint — resuming from Step N."

**Precedence rule:** If both `manifest.json` and `<!-- INSERT_SLIDE_N -->` markers exist, HTML markers are authoritative — prefer over manifest's `last_slide`.

If no checkpoint files exist, proceed from Step 1.

---

### Step 1: Gather Content

Collect info in **three batched rounds** (four if presenter/image details needed). Use `ask_user_question` to present multiple questions per round.

**Round 0 — Source material (always ask first):**

Before asking about topic or audience, ask user what content to base presentation on. Use `ask_user_question` multi-select:

"What source material should this presentation be based on?" Options:
- **URLs** — "I have one or more web pages (blog posts, docs, guides)"
- **Documents** — "I have files (PDF, Word, notes, transcripts)"
- **My own knowledge** — "I'll describe the topic and key points myself"
- **Existing slides** — "I have a prior deck I want to rebuild or restyle"

Mandatory even if user already provided content. If so, acknowledge and ask: "I see you shared [URL / document / topic description]. Any additional source material, or is this everything?"

**Processing source material:**

For each source:
- **URLs**: Fetch and store following "Handling URL-based source material" rules below. Multiple URLs: store each as `[topic-slug]-source-N.md` or combined `[topic-slug]-source-content.md` with section dividers.
- **Documents**: Read via `read` tool. Store copy in presentation folder. Extract topic, key points, terminology to pre-fill Round 1/2 defaults.
- **Own knowledge**: No pre-processing — proceed to Round 1.
- **Existing slides**: Read file (HTML, PDF, or PPTX). Extract slide structure, content, styling. Store copy in presentation folder.

After source material collected, proceed to Round 1 with pre-filled defaults from source (topic name, key points, slide count based on content depth).

**Round 1 — Core info (ask all at once):**
- **Topic** and audience
- **Customer** — is this for a specific customer? If yes, get customer name. Use in title slide subtitle and personalize examples throughout deck.
- **Industry** — single-select: Advertising, Media & Entertainment / Financial Services / Healthcare & Life Sciences / Manufacturing / Public Sector / Retail & Consumer Goods / Technology / Telecom / Other. If "Other", ask to specify. Use to tailor examples, use cases, terminology, icons throughout deck.

**Round 2 — Configuration (ask all at once, with smart defaults):**
- **Features to include** (multi-select): Speaker notes, Presenter slide, Executive mode (BLUF-first, 7 slide cap), Custom graphics

> **Agent note:** When exec mode selected, follow exec deck plan in Step 2 and action-title rules in Content Rules #20.
- **Slide count preference** — auto-suggest from topic complexity: simple (overview, intro) → 7; moderate (architecture, workshop) → 12–15; deep-dive (technical, hands-on, training) → 20–25. User can override.
- **Key points** to cover (or offer to suggest from topic)
- **Brand/accent color** — auto-select from `references/accent-colors.md` by topic keywords. Present suggestion with override option.
- **Title slide logo** — three options: (1) Snowflake logo (`assets/snowflake-logo.svg`), (2) custom logo they provide, (3) no logo. If option 2, collect file path (or paste/attach in follow-up).

**Smart defaults from topic detection:**
- **Accent color**: Match topic keywords against `accent-colors.md` table (illustrative only — always read file for authoritative mappings)
- **Exec mode**: If audience contains "VP", "C-suite", "board", "executive", auto-suggest exec mode ON
- **Slide count**: "overview" or "intro" → 7; "architecture" or "workshop" → 12–15; "deep-dive" or "training" → 20–25

**Round 3 — Follow-up (only if needed):**

> [CONDITION: skip entirely if neither Presenter slide nor Custom logo/graphics were selected in Round 2]

Only ask if user selected Presenter slide or Custom logo/graphics in Round 2:
- **Presenter details**: For each presenter: (1) full name, (2) title/role. Optionally ask for headshot — file path **or paste directly into chat**. Presenter count determines layout (see Presenter slide visual rules). Presenter slide does NOT count toward slide max. Max 9 presenters.
- **Image paths**: For custom logos and graphics, collect file paths or let them paste in follow-up. Advise transparent background works best against dark slide theme.

**Handling title slide logo:**
- **Snowflake logo**: Place `{{SNOWFLAKE_LOGO}}` placeholder in HTML during Step 3 — embed phase handles rest. Do NOT write any SVG now.
- **Custom logo (SVG)**: Use `{{LOGO_INLINE:path}}` placeholder (standalone token, not inside `<img>`). If sizing needed, pass CSS as second arg: `{{LOGO_INLINE:path|height:60px;display:block;margin:0 auto}}`. Auto-stamps `role="img"` so `validate_deck.py` skips geometry checks. See `references/graphics-embedding.md`.
- **Custom logo (raster)**: Use `{{IMG:path}}` inside `<img src="...">` tag.
- **No logo**: Omit logo element from title slide entirely.

**Handling images — ask_user_question limitation:** Tool only supports text input and multiple-choice — users **cannot** paste images through it. When asking about headshots or custom graphics:
- Do NOT collect image paths via ask_user_question. Mention in question text that user can provide file path now OR paste/attach in follow-up message.
- Example: "For your headshot, type a file path here, or paste/drop image in next message (type 'done' or any text so you can press Enter)."

**Handling pasted images:** When user pastes image into chat, save to presentation folder:
1. Write to: `[folder]/pasted_<purpose>_<timestamp>.png` (e.g., `acme/cortex-ai/pasted_headshot_1711700000.png`)
2. **Raster images**: use `{{IMG:path}}` in `<img src="...">` tags; **SVG files**: use `{{SVG_INLINE:path}}` as standalone token.
3. For presenter headshots, use that path with `insert_presenter.py --photo`.
4. Inform user: "Got it — I've saved your pasted image to presentation folder."

**Handling user-provided image file paths:** Verify file exists before copying. If not found, inform user: "I couldn't find a file at [path]. Please double-check path or paste image into chat." If exists:
1. Copy file to `[folder]/` (preserving original filename)
2. Use new `[folder]/filename` path in all subsequent references
3. Inform user: "Copied `filename` to presentation folder."

**Source material processing rules** (referenced by Round 0 above):

If user provides document, transcript, or notes, auto-extract elements and propose defaults for each field.

**Handling URL-based source material:** When user provides URL as topic source (blog post, doc page, guide):

1. **Fetch complete content** via `web_fetch`. Do NOT assume single fetch captures everything — check if returned content appears truncated (mid-section end, cut off, or partial metadata).
2. **If truncated**, make additional `web_fetch` calls or use `browser_snapshot` / `browser_navigate` to capture remaining sections. Continue until full page captured.
3. **Store raw content** as `[folder]/[topic-slug]-source-content.md` immediately after fetching. Authoritative reference for all content decisions — persists across context resets so agent never needs to re-fetch.
4. **Never assume partial content sufficient.** If source page has N sections, verify all N present in stored content. If any missing, fetch again or navigate to anchor links.
5. **Add source artifact to `manifest.json`:**
   ```json
   "source_content": {"path": "[topic-slug]-source-content.md", "source_url": "https://...", "status": "complete"}
   ```
6. **Pass full stored content** (not summary) to Research Subagent and each slide-building subagent. Reference file path so subagents can read directly if inline content too large.

**After gathering topic and customer, create presentation folder:**

- Derive `[topic-slug]` from topic (lowercase, hyphen-separated, e.g., `cortex-ai-overview`)
- Derive `[customer-slug]` from customer name if provided (lowercase, hyphen-separated, e.g., `acme-corp`)
- Derive `[audience-slug]` from audience (lowercase, hyphen-separated, max 2–3 words, e.g., `exec`, `engineering-team`, `sales-leadership`, `all-hands`)
- Create folder: `[customer-slug]/[topic-slug]/` if customer given, else `[topic-slug]/`
- All artifacts (brief, plan, HTML, images) written to this folder
- Inform user: "Created presentation folder: `[folder-path]`"

**⚠️ MANDATORY STOPPING POINT**: Present questions to user and wait for answers before proceeding. Do NOT skip to planning or building. Even if user's initial message implies topic, confirm all items (topic/audience, customer, industry, slide count, key points, accent color, speaker notes, title logo, custom graphics, presenter slide, executive audience) before Step 2.

**Image collection follow-up:** After Step 1 answers, check if user indicated images (headshots, logos, screenshots) but did NOT yet provide path or paste. If any outstanding, prompt **before** Step 2:
- "You mentioned [headshot / logo / custom graphics]. Paste or drop image(s) here (type any text so you can press Enter), or provide file path. I'll wait before moving to slide plan."
- Do NOT proceed to Step 2 until all referenced images received or user explicitly says to skip.

**Config checkpoint:** After all answers collected, save `[folder]/[topic-slug]-config.yaml`:

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

Also create or update `[folder]/manifest.json` with config artifact status `"complete"`. Ensures agent can resume from config without re-asking if context resets.

---

### Research Subagent

> [CONDITION: skip this section and Step 1.5 if user selects "No" to the research question below]

Before Step 2, ask user if they want research subagent to gather supporting facts, stats, and examples. Ask even if user provided their own notes — research supplements with additional data points.

Use `ask_user_question`: "Would you like me to research your topic to gather supporting statistics, examples, and quotes? This typically takes 1–2 minutes." Options: (1) Yes — run research, (2) No — skip and use only what I've provided.

If **Yes**, launch a **parallel 3-agent research swarm** before Step 2 to build a factual brief. If user provided their own content, include it in all three subagent prompts as additional context.

**Before launching**, inform user: "Researching your topic with a parallel 3-agent swarm — this may take 1–2 minutes."

Launch all three subagents **simultaneously** in a single message:

**Subagent type (all three):** `general-purpose` | **readonly:** `true`

**Agent 1 — Stats & Metrics:**
Prompt: Read `references/research-prompt.md` for accuracy rules and tagging conventions. Focus ONLY on: 4–6 compelling statistics and data points for [TOPIC] targeting [AUDIENCE] in [INDUSTRY]. Tag every fact `[EXTRACTED]` or `[INFERRED]` with citation. Apply `[UNVERIFIED — confirm with customer]` to any organization-specific stats. Return structured markdown: stats/data section only. No narrative, no examples.

**Agent 2 — Examples & Case Studies:**
Prompt: Read `references/research-prompt.md` for accuracy rules and tagging conventions. Focus ONLY on: 2–4 real-world examples or customer use cases for [TOPIC] targeting [AUDIENCE] in [INDUSTRY]. Also find 1–2 strong quotes from credible sources ([EXTRACTED] only — no fabricated quotes). Tag every item with source. Return structured markdown: examples and quotes sections only.

**Agent 3 — Concepts, Objections & Narrative:**
Prompt: Focus ONLY on: key terminology and concepts [AUDIENCE] needs to know for [TOPIC], 3–5 common objections or questions the audience may raise, and a suggested narrative arc. If `exec_mode` is `[EXEC_MODE]` and true: narrative arc MUST be conclusion → evidence → context (BLUF). Otherwise: problem → insight → solution → outcome. Return structured markdown: concepts, objections, narrative arc sections only.

**After all three return**, merge into a single brief in this order: stats/data → examples → quotes → concepts → objections → narrative arc. Apply `[UNVERIFIED — confirm with customer]` prefix to any organization-specific stats not already tagged. If any agent returned an error or empty result, launch a single fallback subagent using the full `references/research-prompt.md` prompt (with `[TOPIC]`, `[AUDIENCE]`, `[KEY_POINTS]`, `[EXEC_MODE]` substituted) to cover the missed sections.

Use merged brief as factual foundation for slide copy in Step 2.

**⚠️ Accuracy calibration — wrong is 3× worse than unknown:** Before using any fact from brief in slide copy, check its tag:
- `[EXTRACTED]` — use directly; cite source in speaker notes.
- `[INFERRED]` — present to user for confirmation before writing into slide copy.
- `[UNVERIFIED — confirm with customer]` — MUST be confirmed during Step 1.5 before placing in deck. Wrong stat costly to fix — appears in multiple places: stat cards, SVG `<text>` labels, speaker notes, tooltips, bullet lists. **If fact can't be confirmed, omit it — never use researched estimate.**

**Checkpoint:** Save full brief (tags and citations intact) to `[folder]/[topic-slug]-brief.md` immediately after subagent returns. Citable research artifact — do NOT strip or summarize tags/sources when saving. Update `manifest.json` with brief artifact status.

**URL validation (mandatory after saving brief):** Extract every URL from brief and verify it resolves. Script accepts any text file (markdown or HTML) and checks all URLs. Run:
```bash
python scripts/run_script.py validate_urls.py [folder]/[topic-slug]-brief.md
```
For any URL returning non-200 or timeout:
1. Mark `[DEAD LINK]` inline in brief file
2. Do NOT use as citation in slide copy or speaker notes
3. If only citation for key fact, downgrade from `[EXTRACTED]` to `[INFERRED]` and note dead link

This validation runs on brief — HTML link validation in Step 3 is separate check on deck links.

**Bot-detection fallback:** If `validate_urls.py` reports `403-bot-blocked`, use `web_fetch` to validate individually. If `web_fetch` returns content, URL is valid — ignore 403. If `web_fetch` also fails, URL is genuinely broken.

---

### Step 1.5: Verify Research Brief

> [CONDITION: skip entirely if Research Subagent was not run]

**Skip if user chose not to run Research Subagent.** Proceed to Step 2.

**⚠️ MANDATORY STOPPING POINT**: After research subagent returns and brief is saved, present brief to user. Highlight:

- `[EXTRACTED]` — may use directly; cite source in speaker notes. Present for awareness, no confirmation required.
- `[INFERRED]` — ask user to confirm or reject each one
- `[UNVERIFIED — confirm with customer]` — MUST be confirmed or removed before placing in deck. Wrong stat costly to fix — appears in multiple places: stat cards, SVG `<text>` labels, speaker notes, tooltips, bullet lists.
- Any dead links from `validate_urls.py` — note which facts lost their citation
- Suggested narrative arc — confirm matches user's intent. If rejected, update brief before saving.

Do NOT proceed to Step 2 until user reviews and approves brief. Apply corrections (rejected facts, updated numbers, alternative sources) and save corrected brief to `[folder]/[topic-slug]-brief.md`.

If user rejects or cannot confirm a fact, remove entirely — never leave unconfirmed fact in brief. **If fact can't be confirmed, omit it.**

---

### Step 2: Plan the Slide Deck

Map each slide to a visual component from the catalog listed in the Visual Components section above (do NOT read `references/visual-components.md` — it contains full HTML templates for subagents, not needed for planning). Present plan:

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

**⚠️ MANDATORY STOPPING POINT**: Present slide plan to user. Do NOT proceed to Step 3 until user explicitly approves.

**Executive deck plan (exec_mode):**

> [EXEC MODE ONLY — skip if `exec_mode: false`]

When `exec_mode` true, use BLUF-first structure instead of standard flow:

```
Slide 1: Title -- "Topic Name" with subtitle + accent gradient
Presenter: [if requested] (does not count toward slide max)
Slide 2: Executive Summary -- BLUF: state the recommendation or key conclusion directly (use CTA Block or Stat Callout — no bullets)
Slide 3: Context -- ONE slide max: brief "why this matters" (not a full setup sequence)
Slide 4–6: Supporting Evidence -- Prove the recommendation with data, comparisons, or examples
Slide 7: Call to Action -- Specific ask with a clear next step and owner
```

Executive deck rules:
- **Cap at 7 content slides.** Executives don't read long decks — if content won't fit, cut it.
- **No Agenda slide.** Skip entirely — executives prefer to reach the point immediately.
- **No setup/problem-framing before BLUF.** Slide 2 is always the recommendation, not context.

**Checkpoint:** Once user approves, save full slide plan to `[folder]/[topic-slug]-plan.md` before build. Update `manifest.json`.

---

## Slide Structure

> **SUBAGENT-ONLY REFERENCE**: Do NOT read `references/slide-structure.md` — it is embedded in the subagent bundle. The summary below is for planning context only.

Slide flow, exec deck structure, Presenter/Agenda/BLUF rules, and visual layout guidelines are defined in `references/slide-structure.md` (delivered to subagents via the bundle).

---

## Content Rules

> **SUBAGENT-ONLY REFERENCE**: Do NOT read `references/content-rules.md` — it is embedded in the subagent bundle. The summary below is for planning context only.

All 20 content rules (always-apply rules 1–13 and conditional rules 14–20) are defined in `references/content-rules.md` (delivered to subagents via the bundle).

---

## HTML Output

> **SUBAGENT-ONLY REFERENCE**: Do NOT read `references/html-output-spec.md` — it is embedded in the subagent bundle. The summary below is for planning context only.

Layout, color palette, typography scale, navigation, transitions, and speaker notes specs are defined in `references/html-output-spec.md` (delivered to subagents via the bundle).

---

## Visual Components

> **SUBAGENT-ONLY REFERENCE**: Do NOT read `references/visual-components.md` — it is embedded in the subagent bundle. The component name catalog below is for Step 2 planning only.

Every slide MUST have visual component. Text-only slides not allowed.

Component catalog (full HTML templates delivered to subagents via bundle): Card Grid, Comparison Panel, Stat Callout, Step Flow, Quote Block, Icon + Label List, Code Block, Timeline, Image + Caption, Metric Dashboard, Architecture Diagram, Progress Ring, Animated Counter, Gradient Illustration, Inline SVG Diagram, Custom Graphic, Table, Two-Column Layout, CTA Block, Callout Banner, Tag / Badge Row, Vertical Bar Chart, Horizontal Bar Chart, Line / Area Chart, Donut Chart.

---

### Step 3: Build the HTML

Generate single self-contained HTML file following Slide Structure, HTML Output, and Content Rules above. Every slide MUST have a visual component from the catalog listed in the Visual Components section above.

**Before starting**, inform user: "Building slide deck — may take a few minutes while generating slides."

**Before writing any HTML, read `references/slide-build-protocol.md`** — defines subagent prompt block, batch loop, insert/verify/embed phases, and slide ID rules. This is the only build-phase reference the main agent reads directly.

**Do NOT read the other 8 reference files** (`presentation-runtime.md`, `slide-structure.md`, `content-rules.md`, `html-output-spec.md`, `visual-components.md`, `css-animations.md`, `accent-colors.md`, `graphics-embedding.md`) at build time. They are compressed into `references/subagent-bundle.md` which gets embedded in each subagent prompt. (`accent-colors.md` is read at Step 1 for color selection — do not re-read it here.) Reading them into main context at Step 3 wastes ~10,000 words for no benefit.

**Build mode:** All HTML generation delegated to subagents. Main context orchestrates: reads `slide-build-protocol.md`, launches subagents (passing `references/subagent-bundle.md` + `references/material-icons.md` by embedding their contents in each subagent prompt), checks progress, handles embed/QR/validation. Keeps HTML and reference content out of main context, preserving room for iteration.

**Inlining Snowflake logo (if selected in Step 1):** Place bare `{{SNOWFLAKE_LOGO}}` token on its own line as **first child inside `.slide-inner`** on title slide (before `<h3>` eyebrow). `embed_image.py` replaces it automatically — do NOT read SVG file, do NOT write `<svg>` or `<path>` markup.

**Shell-First, Slide-by-Slide Build (required for all decks):**

Always build in three phases: shell → batched slide insertion → embed. File saved after every slide — worst-case interruption loses one slide in progress.

#### Phase 1 — Generate shell (script):

Run `generate_shell.py` via `run_script.py`. Deterministic script — no subagent, no LLM tokens, completes in under a second. Read slide count and settings from approved plan and config before running.

```bash
python scripts/run_script.py generate_shell.py \
  --title "[Deck Title]" \
  --accent "[accent_color from config]" \
  --slides [N] \
  --output [folder]/[topic-slug]-[audience-slug]-slides.html \
  [--no-notes]   # omit if speaker_notes: true in config
```

Script:
- Reads `templates/shell_template.html`
- Substitutes `{{TITLE}}`, `{{ACCENT}}`, `{{SLIDE_COUNT}}`
- Strips or keeps speaker-notes CSS/HTML/JS based on `--no-notes`
- Runs 4 built-in checks (INSERT_SLIDE_1 marker, total counter, counter div, accent color) and exits non-zero on failure
- Prints: `Shell saved to [path]. Total slide count: N.`

If non-zero exit, read error output and fix arguments — do NOT fall back to subagent. Common errors: wrong output path, missing `--accent`, slide count mismatch.

After success, update `manifest.json` with `html: {status: "shell_complete", "last_slide": 0}`. Inform user: "Shell saved — building slides now."

### Step 3.5: Shell Verification

After `generate_shell.py` succeeds, built-in checks have already passed. Quick confirmation before Phase 2:

1. Confirm output file exists at expected path
2. Confirm printed slide count matches approved plan

If either fails, re-run with corrected arguments. If both pass, proceed to Phase 2.

#### Phase 2 — One subagent per slide (Step 3, continued):

> **GATE**: Read Phase 2 instructions now — only after Phase 1 shell is confirmed complete and Step 3.5 passes. Do not pre-read during Steps 0–2 planning.

Read `references/slide-build-protocol.md` for the parallel batch build protocol. Slides are generated in batches of 4 simultaneously — each subagent generates and **writes** its slide HTML to `{deck_folder}/drafts/slide_N.html` without editing the main file. Main agent calls `insert_slide.py` to insert each draft sequentially. Also covers verification, manifest updates, post-build embed/QR/URL phases, and slide ID/numbering rules.

---

### Step 4: Save and Preview

Save as `[folder]/[topic-slug]-[audience-slug]-slides.html`. Update `manifest.json` with html artifact status `"complete"`.

Open in default browser:
```bash
open [folder]/[topic-slug]-[audience-slug]-slides.html
```

If `open` fails, try `xdg-open` (Linux) or provide file path for manual opening.

---

### Step 5: Verify

**Validation Subagent:**

Inform user: "Validating deck — may take a minute." Delegate automated validation and fix cycle to subagent — keeps error output and large HTML reads out of main context.

**Subagent type:** `general-purpose` | **readonly:** `false`

Prompt: Read `references/validation-prompt.md` and use full contents as subagent prompt, substituting `[folder]`, `[topic-slug]`, `[audience-slug]`, `[skill-root]` with current values.

**Visual QA (after validator passes):**

Open deck (`open [deck.html]`) and use `browser_take_screenshot` for key slides. If screenshot tool unavailable or can't capture `file://` URL, ask user to visually confirm instead.

Capture (best-effort):
1. **Title slide** — logo rendering, gradient background, text hierarchy
2. **One representative content slide** (SVG diagram or card grid) — visual component rendering, spacing, accent color
3. **Last content slide** — CTA/takeaway rendering
4. **QR appendix** (if present) — QR codes scannable (black on white)

If captured, save to `[folder]/screenshots/` (create directory if needed). If not possible, present inline.

Then manually verify:
- Accent color consistent across all slides
- Material Icons render correctly (not as text)
- Animations fire on slide enter
- Navigation works (arrow keys, counter visible)
- **All external links return HTTP 200** — re-run URL validation if skipped or if links added during iteration
- **SVG diagrams (check each slide with inline SVG):**
  - No `<rect>` elements overlap in same column — confirm `y + height` < `y` of next
  - No `<text transform="rotate(` — rotated text signals layout problem
  - `max-height` on SVG containers >= 58vh — lower causes excess empty space
  - No unverified customer facts in `<text>` elements — grep for numbers and proper nouns inside `<text>` tags

If any check fails, fix HTML and re-preview before proceeding.

---

### Step 6: Iterate

Ask: "Take a moment to review. Let me know any changes — wording, adding/removing slides, reordering, custom graphics, color tweaks, anything. Happy to iterate until it's right."

**⚠️ MANDATORY STOPPING POINT**: Wait for user feedback before making changes.

**Common iteration patterns:**
- **Wording / copy edit**: Edit HTML directly. Re-run validator if change touches list, link, or SVG `<text>`.
- **Add slide**: Insert HTML, renumber all subsequent `id="sN"` in reverse order (highest first), update `<span id="total">`, re-run validator.
- **Remove slide**: Same renumbering. If removed slide was in stat card grid, also update `grid-template-columns:repeat(N,1fr)`.
- **Change accent color**: Global find-replace old hex. Check SVG fills and stroke colors also updated.
- **Add/remove external link**: Re-run `generate_qr_appendix.py` — idempotent, rebuilds QR appendix.
- **Any structural change**: Re-run `validate_deck.py --context 5` before presenting updated deck.

**When user signals they're done** (e.g., "looks good", "I'm happy with it", "no more changes", "done", "ship it"): offer PowerPoint export before closing out. Use `ask_user_question`: "Deck is finalized! Would you like me to export a PowerPoint (.pptx) version? Slides are exported as high-resolution screenshots with speaker notes preserved." Options: (1) Yes — export to PowerPoint, (2) No — we're done. If **Yes**, proceed to Step 7.

---

### Step 7: Export to PowerPoint (optional)

> [Triggered by Step 6 offer or direct user request. Skip if user declined or never asked.]

**Prerequisites (one-time per machine):** Download Playwright's Chromium before first use. Skip if already done:

```bash
uv run python -m playwright install chromium
```

**Export command:**

```bash
python scripts/run_script.py export_to_pptx.py <deck.html>
```

Output saved to same folder as HTML with `.pptx` extension.

**Tell user:**
- Slides exported as high-resolution screenshots — text and shapes are images, not editable in PowerPoint.
- Speaker notes preserved in PowerPoint notes pane.
- Opens in PowerPoint, Keynote, or Google Slides (File > Import).

For full details, prerequisites, and error troubleshooting see `references/export-to-pptx.md`.
