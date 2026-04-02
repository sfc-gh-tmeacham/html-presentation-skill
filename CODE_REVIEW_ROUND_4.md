# Code Review — Round 4

**Date:** 2026-04-02  
**Scope:** All 10 Python scripts in `html-presentation/scripts/`  
**Method:** 5 parallel review agents (2 scripts each)  
**Total issues found:** 29

---

## Tier 1 — Bug / Safety

| # | File | Line(s) | Severity | Issue |
|---|---|---|---|---|
| 1 | `color_swap_svg.py` | 211 | Bug | No end-of-value boundary in substitution regex: `#000` matches inside `#0000ff`, silently corrupting long hex values (e.g. `fill="#0000ff"` → `fill="#fff0ff"`) |
| 2 | `color_swap_svg.py` | 224 | Bug | `to_color` is interpolated raw into an `re.subn` replacement string; if `to_color` contains `\1`, `\g<1>`, or a bare `\`, the regex engine misinterprets it as a backreference, producing wrong output or raising `re.error` |
| 3 | `insert_presenter.py` | 277–281 | Bug | `find_insertion_point` may return `<!-- Agenda -->` (no slide number); `insert_slide` immediately calls `re.search(r'Slide (\d+)', ...)` on it, finds nothing, and exits with an error — always fails on decks whose Agenda comment has no number |
| 4 | `insert_presenter.py` | 219–221 | Bug | `re.search(r'<!-- Agenda.*?-->')` has no `re.DOTALL`; a multiline comment (`<!--\n Agenda\n-->`) silently fails to match |
| 5 | `svg_optimize.py` | 247 | Safety | `output_path.write_text(...)` is not atomic; an interrupted write leaves a corrupt/truncated SVG; every other file-writing script in the codebase uses `mkstemp + os.replace` |
| 6 | `resize_image.py` | 132–136, 148–152 | Safety | Both the `shutil.copy2` path and the `resized.save()` path write directly; no atomic write protection on either output path |
| 7 | `color_swap_svg.py` | 320 | Safety | `output_path.write_text(...)` is not atomic (same issue as svg_optimize.py) |
| 8 | `generate_qr_appendix.py` | 197–198 | Safety | `url` and `title` are interpolated into the generated slide HTML without `html.escape()`; `&` in query strings produces invalid HTML; titles or anchor text containing `<` or `>` break the markup |
| 9 | `insert_presenter.py` | 125–133, 163–166 | Safety | Presenter `name` and `title` are injected into HTML without escaping; a name like `x" onerror="alert(1)` breaks attributes or produces an XSS vector in the rendered slide |

---

## Tier 2 — Logic

| # | File | Line(s) | Issue |
|---|---|---|---|
| 10 | `svg_optimize.py` | 50–65 | `STRIP_ATTRS` patterns use `"[^"]*"` (double-quote only); single-quoted attributes like `xml:space='preserve'` are never removed |
| 11 | `svg_optimize.py` | 40–44 | Self-closing `<metadata/>`, `<sodipodi:namedview/>`, `<defs />` (space before `/>`) not stripped — the `<tag>...</tag>` patterns require a closing tag |
| 12 | `svg_optimize.py` | 158–175 | `except re.error` in the substitution loop can never trigger — `re.error` is only raised at compile time, never during `pattern.sub()` on a pre-compiled pattern; the warning is dead code |
| 13 | `embed_image.py` | 107–111 | MIME type is derived from the **file extension**, not Pillow's detected format; a PNG renamed to `.jpg` generates `data:image/jpeg;<PNG bytes>`, which browsers reject |
| 14 | `embed_image.py` | 159, 192, 210 | `per_token_size or default_max_size` treats `0` as falsy (silent fallback) and allows negative values through, which cause a confusing Pillow `ValueError` deep in the stack |
| 15 | `color_swap_svg.py` | 171 | `list(set(v.lower() for v in variants))` has non-deterministic ordering; substitution order varies across Python versions, making the output non-reproducible |
| 16 | `generate_qr_appendix.py` | 307 | `new_total = last_num + total_pages` assumes sequential IDs; for a deck with gaps (e.g. s1, s2, s5), `last_num=5` but there are 3 slides, writing the wrong total to `<span id="total">` |
| 17 | `insert_presenter.py` | 292–296 | Slide renumber regex uses `\b` before `id`; `\b` matches at `data-slide-id` (hyphen → word boundary), so those attributes are incorrectly renumbered |
| 18 | `insert_presenter.py` | 306–309 | `html.replace(f'<span id="total">{current_total}</span>', ...)` missing `count=1` — if the total span appears twice the counter is double-updated |
| 19 | `validate_deck.py` | 75, 77, 81 | All three slide-matching regexes require `class` before `id` in the tag; `<div id="s1" class="slide">` is completely invisible to slide-count, visual-check, and word-count passes |
| 20 | `validate_deck.py` | 87 | `ALT_RE` only matches double-quoted `alt="..."` — an `<img alt='text'>` generates a false "missing alt" warning |
| 21 | `validate_deck.py` | 313–317 | `TEXT_ALIGN_LEFT_RE` only inspects the inline `style="..."` attribute of `<ul>`/`<ol>` tags; alignment applied via a CSS class generates spurious warnings for every list element |
| 22 | `validate_deck.py` | 326–338 | `SVG_CONTAINER_RE.finditer(html)` matches every `max-height` in the document regardless of element type; a `max-height:50vh` on a paragraph triggers a false "SVG container too low" warning |
| 23 | `screenshot_to_slide.py` | 134–135, 169 | The `except Exception` handler in `auto_crop` returns `img`, but `img` is only reassigned to RGBA if `img.convert("RGBA")` succeeds; an exception before that point silently returns the original non-RGBA image, breaking the RGBA contract for all callers |
| 24 | `run_script.py` | 247 | `--reinstall` is stripped from **all** argv positions including those after the script name; a child script that legitimately accepts `--reinstall` will never see it |
| 25 | `run_script.py` | 284 | `os.execv(venv_python, cmd)` is unguarded; if the venv binary exists but is not executable, an unhandled `OSError` crashes with a raw traceback instead of a clean error message |

---

## Tier 3 — Consistency / Dead code / Style

| # | File | Line(s) | Issue |
|---|---|---|---|
| 26 | `generate_qr_appendix.py` | 108, 128, 130, 163–174, 270, 280 | 8 inline `re.compile`/`re.search`/`re.sub` calls in helper functions; established pattern is module-level constants |
| 27 | `generate_qr_appendix.py` | 287, 339 | `accent = extract_accent(html)` is computed and printed but never passed to any HTML-generating function — dead work |
| 28 | `embed_image.py` | 225, 231 | `raw_bytes` returned from `encode_file()` is unpacked but never referenced; `total_bytes` accumulates `len(data_uri)` instead |
| 29 | `resize_image.py` | 103 | `Image.open()` result not used as a context manager — the file handle stays open until GC rather than being released explicitly |

---

## Fix Status

| # | File | Status |
|---|---|---|
| 1 | `color_swap_svg.py` | ✅ |
| 2 | `color_swap_svg.py` | ✅ |
| 3 | `insert_presenter.py` | ✅ |
| 4 | `insert_presenter.py` | ✅ |
| 5 | `svg_optimize.py` | ✅ |
| 6 | `resize_image.py` | ✅ |
| 7 | `color_swap_svg.py` | ✅ |
| 8 | `generate_qr_appendix.py` | ✅ |
| 9 | `insert_presenter.py` | ✅ |
| 10 | `svg_optimize.py` | ✅ |
| 11 | `svg_optimize.py` | ✅ |
| 12 | `svg_optimize.py` | ✅ |
| 13 | `embed_image.py` | ✅ |
| 14 | `embed_image.py` | ✅ |
| 15 | `color_swap_svg.py` | ✅ |
| 16 | `generate_qr_appendix.py` | ✅ |
| 17 | `insert_presenter.py` | ✅ |
| 18 | `insert_presenter.py` | ✅ |
| 19 | `validate_deck.py` | ✅ |
| 20 | `validate_deck.py` | ✅ |
| 21 | `validate_deck.py` | ⏭ skipped — requires CSS class parsing |
| 22 | `validate_deck.py` | ✅ |
| 23 | `screenshot_to_slide.py` | ✅ |
| 24 | `run_script.py` | ✅ |
| 25 | `run_script.py` | ✅ |
| 26 | `generate_qr_appendix.py` | ✅ |
| 27 | `generate_qr_appendix.py` | ✅ |
| 28 | `embed_image.py` | ✅ |
| 29 | `resize_image.py` | ✅ |
