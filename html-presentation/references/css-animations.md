# CSS Animation Patterns

Use animations when they help the audience understand content — revealing steps in order, drawing attention to key numbers, showing relationships. Never animate just for decoration.

## When to Animate

| Situation | Animation | Why it helps |
|-----------|-----------|-------------|
| Slides entering the viewport | Fade-in + slide-up | Guides the eye onto the new slide |
| Sequential process / flow steps | Staggered fade-in | Reinforces the order of steps |
| Stat cards with numbers | Counter roll-up | Draws attention to key metrics, implies dynamism |
| Progress rings | Fill animation | Communicates magnitude more intuitively than a static ring |
| Architecture diagrams with arrows | Draw-on / dash animation | Shows data flow direction |
| Live / active status indicators | Pulse or breathing glow | Communicates "running" or "active" state |
| Hover on interactive cards | Scale + border glow | Signals interactivity |
| Comparison panels / two-column layouts | Slide-in from sides | Pairs elements as opposing forces entering from opposite directions |
| Stat callouts and key numbers | Scale pop (spring) | More impactful than fade+slide; makes numbers feel significant |
| Code reveals, terminal demos | Typewriter | Builds anticipation; simulates live typing |
| Product demo / loading state slides | Shimmer sweep | Implies data loading or pipeline activity |
| Title slides and section dividers | Gradient shift | Adds ambient depth without distracting motion |
| Highlighted cards or callouts | Border glow pulse | Draws attention without moving the element |

## When NOT to Animate

- Static comparison panels or tables (the audience needs to scan, not wait)
- Code block text: avoid CSS clip sweeps or full-block fades that hide content mid-read; use the JS typewriter (Pattern 14) instead — it reveals characters in sequence while preserving syntax-highlight span coloring
- Body text or quote blocks (let the content be immediately readable)
- Anything that loops infinitely unless it represents a live/ongoing state (exceptions: pulse for "live", shimmer for "loading", gradient-shift for ambient title backgrounds)

## Approved Patterns

### 1. Fade-in on slide enter
```css
.anim { opacity: 0; transform: translateY(24px); transition: opacity 0.6s ease, transform 0.6s ease; }
.anim.visible { opacity: 1; transform: translateY(0); }
```

### 2. Staggered children
```css
.stagger > *:nth-child(1) { transition-delay: 0s; }
.stagger > *:nth-child(2) { transition-delay: 0.1s; }
.stagger > *:nth-child(3) { transition-delay: 0.2s; }
.stagger > *:nth-child(4) { transition-delay: 0.3s; }
```

### 3. Progress bar fill
```css
.progress-fill { width: 0; transition: width 1s ease; }
.progress-fill.visible { width: var(--target-width); }
```

### 4. SVG progress ring
```css
.ring-fill { stroke-dasharray: 283; stroke-dashoffset: 283; transition: stroke-dashoffset 1.2s ease; }
.ring-fill.visible { stroke-dashoffset: var(--target-offset); }
```

### 5. Counter roll-up
```css
@property --num { syntax: '<integer>'; initial-value: 0; inherits: false; }
.counter { --num: 0; transition: --num 1.5s ease; counter-reset: num var(--num); font-variant-numeric: tabular-nums; }
.counter::after { content: counter(num); }
.counter.visible { --num: var(--target); }
```

### 6. Pulse indicator (live status)
```css
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.6; transform: scale(1.8); } }
.pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); position: relative; }
.pulse-dot::after { content: ''; position: absolute; inset: 0; border-radius: 50%; background: inherit; animation: pulse 2s ease-in-out infinite; }
```

### 7. SVG line draw
```css
@keyframes draw { to { stroke-dashoffset: 0; } }
.draw-line { stroke-dasharray: 200; stroke-dashoffset: 200; }
.draw-line.visible { animation: draw 1s ease forwards; }
```

### 8. Slide-in from sides
Elements enter from the left and right simultaneously — ideal for comparison panels or two-column layouts.
```css
.anim-left  { opacity: 0; transform: translateX(-40px); transition: opacity 0.6s ease, transform 0.6s ease; }
.anim-right { opacity: 0; transform: translateX( 40px); transition: opacity 0.6s ease, transform 0.6s ease; }
.anim-left.visible, .anim-right.visible { opacity: 1; transform: translateX(0); }
```
Apply `.anim-left` to the left column and `.anim-right` to the right column. Add the same `visible` class toggle used for `.anim`.

### 9. Scale pop (spring entrance)
Element scales up from nothing with a slight overshoot — more impactful than fade+slide for stat callouts and hero numbers.
```css
@keyframes scalePop {
  0%   { opacity: 0; transform: scale(0.6); }
  70%  { opacity: 1; transform: scale(1.08); }
  100% { opacity: 1; transform: scale(1); }
}
.scale-pop { opacity: 0; }
.scale-pop.visible { animation: scalePop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards; }
```
The cubic-bezier `(0.34, 1.56, 0.64, 1)` produces a natural spring overshoot. Use sparingly — one or two elements per slide maximum.

### 10. Typewriter
Text appears character by character using CSS `steps()`. Best for short strings (command names, key terms, one-liners).
```css
@keyframes typing   { from { width: 0; } to { width: 100%; } }
@keyframes blinkCaret { 0%, 100% { border-color: transparent; } 50% { border-color: var(--accent); } }

.typewriter {
  display: inline-block;
  overflow: hidden;
  white-space: nowrap;
  width: 0;
  border-right: 2px solid var(--accent);
}
.typewriter.visible {
  animation:
    typing     2s steps(40, end) forwards,
    blinkCaret 0.75s step-end 3;
}
```
Adjust `steps(40)` to match the approximate character count of the string. The caret blinks 3 times then disappears. Wrap only the target string — not the full paragraph.

### 11. Shimmer sweep
An animated gradient that sweeps across a card, implying data loading or pipeline activity.
```css
@keyframes shimmer { to { background-position: 200% center; } }

.shimmer {
  background: linear-gradient(
    90deg,
    var(--card) 25%,
    rgba(255,255,255,0.07) 50%,
    var(--card) 75%
  );
  background-size: 200% auto;
  animation: shimmer 1.8s linear infinite;
  border-radius: 12px;
}
```
Apply `.shimmer` to a card or placeholder element. Pair with a label like "Processing…" or "Loading data" for context. Because this loops infinitely, only use it to represent an active/ongoing state — remove the class or swap to a static card once the "loaded" state is shown.

### 12. Gradient shift
A slowly animating background gradient for title slides and section dividers that adds depth without distraction.
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
Apply to the slide wrapper or a decorative `div` behind the content. Use subtle dark hues offset by the accent color tint — avoid bright or saturated colors that fight the slide text.

### 13. Border glow pulse
A repeating box-shadow pulse that draws attention to a highlighted card without moving it.
```css
@keyframes borderGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(41,181,232,0); border-color: var(--border); }
  50%       { box-shadow: 0 0 0 6px rgba(41,181,232,0.25); border-color: var(--accent); }
}

.glow-pulse {
  border: 1px solid var(--border);
  border-radius: 16px;
  animation: borderGlow 2s ease-in-out infinite;
}
```
Replace the hardcoded `rgba(41,181,232,...)` with the deck's actual accent color at 25% opacity. Use only on one card per slide — applying to multiple elements simultaneously looks cluttered.

### 14. Code block typewriter (JS — multi-line with syntax coloring)
Character-by-character reveal that preserves syntax-highlight `<span>` coloring. Locks the container to its full-height before animating so the slide layout never shifts. A blinking accent cursor tracks the insertion point and disappears 800 ms after typing completes.

**Required CSS** — add to the deck `<style>` block:
```css
@keyframes blinkCaret { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.tw-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--accent);
  vertical-align: text-bottom;
  animation: blinkCaret 0.7s step-end infinite;
  margin-left: 1px;
}
@media (prefers-reduced-motion: reduce) { .tw-cursor { animation: none; } }
.tw-pending,
.tw-pending span { color: transparent !important; }
```

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
- Add `white-space: pre-wrap` on `.code-block` (required regardless of animation).
- For `prefers-reduced-motion`: skip `twTypewrite`, leave `cb.innerHTML = SOURCE`.

## Rules

- All animations MUST respect `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```
- Animations fire once only (no infinite loops) unless representing an ongoing state (e.g., pulse for "live").
- Keep durations between 0.3s and 1.5s. Anything longer feels sluggish.
- Use `ease` or `ease-out` for enters; `ease-in` for exits. Avoid `linear` for UI motion.
- The slide must be fully readable if animations fail to run (progressive enhancement).
