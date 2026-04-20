## Shell Safety Rule

**NEVER use heredoc syntax** (`<<EOF`, `<<'EOF'`, `cat <<EOF`) or multi-line `python3 -c "..."` strings in bash. These cause the terminal to hang indefinitely. If you need to write content to a file, use the `write` tool first, then reference the file path in bash.

---

Validate and fix the HTML slide deck at: [folder]/[topic-slug]-[audience-slug]-slides.html
Working directory: [skill-root]/ (the parent of the presentation folder, where `scripts/` is located).

Step 1: Run the validator with context enabled:
  python scripts/run_script.py validate_deck.py [folder]/[topic-slug]-[audience-slug]-slides.html --context 5

  The `--context 5` flag prints +/-5 lines around each warning/failure, with any base64
  content automatically redacted to `[base64 data omitted — Nkb]`. This gives you all
  the context needed to make each fix. **Do NOT use the Read tool to open the HTML file
  directly** — the validator output is sufficient and avoids base64 flooding your context.

Step 2: For each reported issue, apply the fix using the Edit tool with the exact
  surrounding text shown in the context snippet. Each message includes a slide ID and
  line number (e.g. `s10 line 450 →`) to pinpoint the location.

  Key fix rules (from SKILL.md Content Rules and HTML Output):
  - SVG containers: `max-height` >= 58vh (lower values cause excess empty slide space)
  - No `transform="rotate("` on `<text>` elements (rotated text = layout problem)
  - Lists with icon markers: parent `<ul>` must set `list-style: none; padding: 0;`
  - All `<a>` tags: must have `target="_blank" rel="noopener"`
  - Bulleted lists: must use `text-align: left` even inside centered containers
  - SVG stacked rects: `y_N + height_N + 10 < y_(N+1)` (no overlapping, 10px min gap)
  - No `display:none` for slide transitions — use `opacity` + `pointer-events` only
  - Code blocks: first content must be on the same line as the `<div class="code-block">` opening tag — a leading newline renders as a visible blank line due to `white-space: pre-wrap`

Step 3: Re-run the validator with --context 5. Repeat until it passes or until you have made 3 fix attempts.

Return a one-line summary: "PASS — N slides, all checks clean" or "Fixed N issues: [brief list]". If validation still fails after 3 attempts, list the remaining errors.
