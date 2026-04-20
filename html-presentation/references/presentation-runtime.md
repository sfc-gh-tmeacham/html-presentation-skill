# Presentation Runtime

The shell template provides the complete navigation, slide transitions, and speaker notes system. Subagents never write or copy this infrastructure — it is pre-built in every generated shell.

---

## What the Shell Provides

- **`#nav` pill** — fixed bottom-right pill with ← / → arrow buttons, slide counter (`curr / total`), and notes hint. The `<div class="counter"></div>` marker immediately before it is required by `generate_qr_appendix.py` as its insertion point — do not remove it.
- **Slide transitions** — all slides use `position:absolute; inset:0; opacity:0` and fade to `opacity:1` via `.slide.active`. **Never toggle `display:none` / `display:flex` on slides** — this breaks CSS `opacity` transitions.
- **Speaker notes** — add `<div class="speaker-notes">...</div>` inside each slide div. `N` opens a popup window (dual-monitor), `B` opens a bottom panel that shrinks the deck upward (single-monitor). Opening one closes the other.
- **Keyboard navigation** — `ArrowRight` / `ArrowDown` = next; `ArrowLeft` / `ArrowUp` = prev; `N` = notes window; `B` = notes panel toggle.
- **`show()` function** — advances slides, fires `.active` class toggle, updates counter and notes. The `switch` keydown handler and `show(0)` init call are both in the shell.

---

## Speaker Notes Formatting

Text the presenter reads aloud is plain prose. Any text **not** meant to be spoken — stage directions, click cues, reminders, asides — MUST be wrapped in square brackets: `[Pause here]`, `[Click to advance]`, `[Reference the chart on the left]`. The presenter skips bracketed content when speaking.

---

## Per-Slide JS Hook

If a slide needs custom JS **beyond what the shell handles automatically**, extend `show()` in a `<script>` block inside the slide or in a deck-level script. Note: `.anim-left`, `.anim-right`, `.scale-pop`, `.draw-line`, `.progress-fill`, `.ring-fill`, `.counter`, and `.typewriter` all have `.visible` toggled automatically by the shell's `show()` — no per-slide JS is needed for these classes. The shell's `show()` signature:

```js
function show(n) {
  slides[current].classList.remove('active');
  current = (n + slides.length) % slides.length;
  slides[current].classList.add('active');
  document.getElementById('curr').textContent = current + 1;
  // updateNotesWindow() and updateNotesPanel() also called here
}
```

Wire per-slide enter/leave logic by checking `current` (or `prev`) after `classList.add('active')`. The shell's `switch` keydown handler uses the canonical form required by the validator — do not replace it with `if/else`.
