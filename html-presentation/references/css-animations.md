# CSS Animation Patterns

Use animations when they help the audience understand content — revealing steps in order, drawing attention to key numbers, showing relationships. Never animate just for decoration.

**Shell note:** CSS for Patterns 1–9 and 11–13 is pre-loaded in every shell. Do NOT copy these rules into slide `<style>` blocks — just use the class names directly. Pattern 10 (`.typewriter`) CSS is not in the shell and must be added per-slide. Pattern 14 CSS is pre-loaded; only the JS needs to be added per-deck.

---

## When to Animate

| Situation | Animation | Pattern |
|-----------|-----------|---------|
| Slides entering the viewport | Fade-in + slide-up | 1 (`.anim`) |
| Sequential process / flow steps | Staggered fade-in | 2 (`.stagger`) |
| Stat cards with numbers | Counter roll-up | 5 (`.counter`) |
| Progress rings | Fill animation | 4 (`.ring-fill`) |
| Architecture diagrams with arrows | Draw-on / dash animation | 7 (`.draw-line`) |
| Live / active status indicators | Pulse | 6 (`.pulse-dot`) |
| Highlighted cards or callouts | Border glow pulse | 13 (`.glow-pulse`) |
| Comparison panels / two-column layouts | Slide-in from sides | 8 (`.anim-left` / `.anim-right`) |
| Stat callouts and key numbers | Scale pop (spring) | 9 (`.scale-pop`) |
| Code reveals, terminal demos | Typewriter | 14 (`twTypewrite`) |
| Product demo / loading state slides | Shimmer sweep | 11 (`.shimmer`) |
| Title slides and section dividers | Gradient shift | 12 (`.gradient-bg`) |

## When NOT to Animate

- Static comparison panels or tables (the audience needs to scan, not wait)
- Code block text: avoid CSS clip sweeps or full-block fades that hide content mid-read; use Pattern 14 instead — it reveals characters in sequence while preserving syntax-highlight span coloring
- Body text or quote blocks (let the content be immediately readable)
- Anything that loops infinitely unless it represents a live/ongoing state (exceptions: pulse for "live", shimmer for "loading", gradient-shift for ambient title backgrounds)

---

## Approved Patterns

### 1. Fade-in on slide enter
**Shell class:** `.anim` — fires automatically via `.slide.active .anim`, no JS needed. Add to any element.

**JS-triggered alternative:** `.anim.visible` is also defined — add `.visible` programmatically for reveal-on-click or other controlled triggers.

---

### 2. Staggered children
**Shell class:** `.stagger` — add to a parent whose children each carry `class="anim"`. Up to 6 children animate in sequence (0s–0.5s delays). Fires automatically with `.anim` — no JS needed.

```html
<div class="card-grid anim stagger">
  <div class="card">...</div>
  <div class="card">...</div>
  <div class="card">...</div>
</div>
```

---

### 3. Progress bar fill
**Shell class:** `.progress-fill` — set `--target-width` inline. **Trigger: automatic** — the shell's `show()` adds `.visible` on slide enter and removes it on leave. No per-slide JS needed.

```html
<div style="height:8px;background:var(--border);border-radius:4px;overflow:hidden;">
  <div class="progress-fill" style="--target-width:75%;height:100%;background:var(--accent);border-radius:4px;"></div>
</div>
```

---

### 4. SVG progress ring
**Shell class:** `.ring-fill` — set `--target-offset` on the `<circle>` (the `stroke-dashoffset` value for the desired fill percentage). **Trigger: automatic** — the shell's `show()` adds `.visible` on slide enter and removes it on leave. No per-slide JS needed.

```html
<circle class="ring-fill" cx="90" cy="90" r="80" fill="none" stroke="var(--accent)"
  stroke-width="12" stroke-linecap="round" transform="rotate(-90 90 90)"
  style="--target-offset:80;"/>
```

---

### 5. Counter roll-up
**Shell class:** `.counter` (with `@property --num` registered). Set `style="--target:N"` to the end value. **Trigger: automatic** — the shell's `show()` adds `.visible` on slide enter and removes it on leave. No per-slide JS needed.

```html
<div class="counter anim" style="font-size:4.5rem;font-weight:800;color:var(--accent);--target:42;"></div>
```

---

### 6. Pulse indicator (live status)
**Shell class:** `.pulse-dot` — fires automatically (infinite loop). Add to an 8px dot element.

```html
<div style="display:flex;align-items:center;gap:10px;">
  <div class="pulse-dot"></div>
  <span style="font-size:0.875rem;color:var(--secondary);">Live</span>
</div>
```

---

### 7. SVG line draw
**Shell class:** `.draw-line` — set `stroke-dasharray` to match line length. **Trigger: automatic** — the shell's `show()` adds `.visible` on slide enter and removes it on leave. No per-slide JS needed.

```html
<line class="draw-line" x1="0" y1="50" x2="400" y2="50"
  stroke="var(--accent)" stroke-width="2"
  style="stroke-dasharray:400;stroke-dashoffset:400;"/>
```

---

### 8. Slide-in from sides
**Shell classes:** `.anim-left`, `.anim-right` — ideal for Comparison Panel columns entering simultaneously. **Trigger: automatic** — the shell's `show()` adds `.visible` on slide enter and removes it on leave. No per-slide JS needed.

```html
<div class="anim-left"><!-- left column --></div>
<div class="anim-right"><!-- right column --></div>
```

---

### 9. Scale pop (spring entrance)
**Shell class:** `.scale-pop` — more impactful than fade+slide for stat callouts and hero numbers. Use sparingly — one or two elements per slide maximum. **Trigger: automatic** — the shell's `show()` adds `.visible` on slide enter and removes it on leave. No per-slide JS needed.

```html
<div class="scale-pop" style="font-size:6rem;font-weight:800;color:var(--accent);">42%</div>
```

---

### 10. Typewriter (CSS — short single-line strings)
**Not in shell — add to slide `<style>` block.** Best for short strings (command names, key terms, one-liners). For multi-line code blocks use Pattern 14 instead.

```css
@keyframes typing     { from { width: 0; } to { width: 100%; } }
@keyframes blinkCaret { 0%, 100% { border-color: transparent; } 50% { border-color: var(--accent); } }
.typewriter {
  display: inline-block; overflow: hidden; white-space: nowrap;
  width: 0; border-right: 2px solid var(--accent);
}
.typewriter.visible {
  animation: typing 2s steps(40, end) forwards, blinkCaret 0.75s step-end 3;
}
@media (prefers-reduced-motion: reduce) { .typewriter { width: 100%; animation: none; } }
```

Adjust `steps(40)` to match the character count. The caret blinks 3 times then disappears. Wrap only the target string — not the full paragraph. **Trigger: automatic** — the shell's `show()` adds `.visible` on slide enter and removes it on leave. No per-slide JS needed.

---

### 11. Shimmer sweep
**Shell class:** `.shimmer` — fires automatically (infinite loop). Apply to a card or placeholder to imply loading/pipeline activity.

```html
<div class="shimmer" style="height:80px;"></div>
```

Only use for "active/loading" states — swap to a static card when the "loaded" state is shown.

---

### 12. Gradient shift
**Shell class:** `.gradient-bg` — fires automatically. Apply to the title slide wrapper.

```html
<div id="s1" class="slide gradient-bg active">
```

---

### 13. Border glow pulse
**Shell class:** `.glow-pulse` — fires automatically (infinite loop). Use on one card per slide maximum.

```html
<div class="card glow-pulse">...</div>
```

Note: the `rgba(41,181,232,...)` tint in `@keyframes borderGlow` is hardcoded to Snowflake Blue. If using a different accent, add an override in the slide's `<style>`: `@keyframes borderGlow { 50% { box-shadow: 0 0 0 6px rgba(R,G,B,0.25); } }`.

---

### 14. Code block typewriter (JS — multi-line with syntax coloring)
Character-by-character reveal that preserves syntax-highlight `<span>` coloring. Locks the container to its full height before animating so the slide layout never shifts. A blinking accent cursor tracks the insertion point and disappears 800 ms after typing completes.

**CSS pre-loaded in shell** (`.tw-cursor`, `.tw-pending`, `@keyframes blinkCaret`) — no CSS to add.

**Required JS** — add once per deck, before the closing `</body>`:
```javascript
function twTypewrite(el, html, speed = 6) {
  let total = 0;
  for (let i = 0; i < html.length; ) {
    if (html[i] === '<') { i = html.indexOf('>', i) + 1; } else { total++; i++; }
  }
  let shown = 0;
  const timer = setInterval(() => {
    if (shown > total) {
      clearInterval(timer);
      el.innerHTML = html;
      return;
    }
    let out = '', count = 0;
    for (let i = 0; i < html.length && count < shown; ) {
      if (html[i] === '<') {
        const end = html.indexOf('>', i);
        out += html.slice(i, end + 1);
        i = end + 1;
      } else { out += html[i]; count++; i++; }
    }
    el.innerHTML = out + '<span class="tw-cursor"></span>';
    shown++;
  }, speed);
}
```

**Wiring up a code block:**
```javascript
// Store the pre-rendered HTML (with syntax spans) at page init
const SOURCE = document.getElementById('my-code-block').innerHTML;

// On slide ENTER
function enterCodeSlide(cb) {
  cb.classList.add('tw-pending');
  setTimeout(() => {
    const h = cb.offsetHeight;
    cb.style.height = h + 'px';
    cb.classList.remove('tw-pending');
    cb.innerHTML = '';
    twTypewrite(cb, SOURCE, 4);
  }, 650);
}

// On slide LEAVE
function leaveCodeSlide(cb) {
  cb.style.height = '';
  cb.classList.remove('tw-pending');
  cb.innerHTML = SOURCE;
}
```

Key rules:
- Store `innerHTML` at page init (before any `show()` call) — not inside the slide-enter handler, or it captures an empty string after first visit.
- Use `.tw-pending` (transparent text) to hold the full-sized container during the delay, not `scrollHeight` — `scrollHeight` is unreliable for off-screen slides.
- Lock `height` with `offsetHeight` inside the `setTimeout` callback, after the slide has been active for ≥ 600 ms. This is the only point where the measurement is guaranteed accurate.
- Release `height` and restore `innerHTML` on slide leave so replay works cleanly.
- For `prefers-reduced-motion`: skip `twTypewrite`, leave `cb.innerHTML = SOURCE`.

---

## Rules

- `prefers-reduced-motion` is handled by the shell for all pre-loaded classes (Patterns 1–9, 11–13). For Pattern 10, add `@media (prefers-reduced-motion: reduce) { .typewriter { width: 100%; animation: none; } }` to the slide `<style>` block.
- Animations fire once only (no infinite loops) unless representing an ongoing state (exceptions: `.pulse-dot`, `.shimmer`, `.gradient-bg`, `.glow-pulse`).
- Keep durations between 0.3s and 1.5s. Anything longer feels sluggish.
- Use `ease` or `ease-out` for enters; `ease-in` for exits. Avoid `linear` for UI motion.
- The slide must be fully readable if animations fail to run (progressive enhancement).
