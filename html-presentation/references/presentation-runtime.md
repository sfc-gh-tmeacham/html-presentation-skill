# Presentation Runtime

Complete HTML, CSS, and JS for the navigation pill, slide transitions, and speaker notes system. Copy these patterns exactly — do not improvise structure.

---

## Navigation

### HTML

The navigation block MUST be preceded by `<div class="counter"></div>` — this empty marker is required by `generate_qr_appendix.py` as its insertion point.

```html
<div class="counter"></div>
<div id="nav">
  <span class="nbtn" id="prev">&#8592;</span>
  <span><span id="curr">1</span> / <span id="total">N</span></span>
  <span class="nbtn" id="next">&#8594;</span>
  <span id="notes-hint">N = notes window &nbsp;&bull;&nbsp; B = notes panel</span>
</div>
```

### CSS

```css
#nav {
  position: fixed;
  bottom: clamp(12px, 2vh, 24px);
  right: clamp(16px, 2vw, 28px);
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(26, 26, 26, 0.9);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 8px 18px;
  font-size: 0.85rem;
  color: var(--secondary);
  backdrop-filter: blur(8px);
  z-index: 100;
}
.nbtn {
  cursor: pointer;
  color: var(--text);
  font-size: 1rem;
  padding: 0 4px;
  transition: color 0.2s;
  user-select: none;
}
.nbtn:hover { color: var(--accent); }
#notes-hint { font-size: 0.72rem; color: #555; margin-left: 4px; }
```

---

## Slide Transitions

All slides use `position: absolute; inset: 0` and fade via `opacity`. Never toggle `display: none / display: flex` — this prevents CSS transitions from working.

```css
.slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.5s ease;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: clamp(1.5rem, 4vh, 3.5rem) clamp(1.5rem, 5vw, 4rem);
}
.slide.active {
  opacity: 1;
  pointer-events: auto;
}
```

---

## Speaker Notes

Two modes, mutually exclusive — opening one closes the other:
- `N` — popup window (ideal for dual-monitor setups)
- `B` — bottom panel that shrinks the slide area upward (ideal for single-monitor)

### CSS

Add after `.speaker-notes { display: none; }`:

```css
#deck { position: relative; width: 100vw; height: 100vh; transition: height 0.3s ease; }
#deck.panel-open { height: calc(100vh - 180px); }
#notes-panel {
  position: fixed; bottom: 0; left: 0; width: 100%; height: 180px;
  background: #111; border-top: 2px solid var(--accent);
  display: none; flex-direction: column; z-index: 99;
}
#notes-panel.open { display: flex; }
#notes-panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 20px 6px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
#notes-panel-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.8px; color: var(--accent); font-weight: 600; }
#notes-panel-slide { font-size: 0.7rem; color: #555; letter-spacing: 1px; }
#notes-panel-close { font-size: 0.7rem; color: #555; cursor: pointer; letter-spacing: 1px; transition: color 0.2s; }
#notes-panel-close:hover { color: #aaa; }
#notes-panel-body { flex: 1; overflow-y: auto; padding: 12px 20px; }
#notes-panel-text { font-size: 1rem; line-height: 1.65; color: #d0d0d0; }
body.panel-open #nav { bottom: calc(180px + clamp(12px, 2vh, 24px)); }
```

### HTML

Add after `#nav`:

```html
<div id="notes-panel">
  <div id="notes-panel-header">
    <span id="notes-panel-label">Speaker Notes</span>
    <span id="notes-panel-slide"></span>
    <span id="notes-panel-close">B = close</span>
  </div>
  <div id="notes-panel-body">
    <div id="notes-panel-text"></div>
  </div>
</div>
```

### JS

```js
let notesWin = null;
let panelOpen = false;

function updateNotesWindow() {
  if (!notesWin || notesWin.closed) return;
  const notes = slides[current].querySelector('.speaker-notes');
  const text = notes ? notes.textContent : '';
  notesWin.document.getElementById('noteText').textContent = text;
  notesWin.document.getElementById('noteSlide').textContent =
    'Slide ' + (current + 1) + ' of ' + slides.length;
}

function updateNotesPanel() {
  if (!panelOpen) return;
  const notes = slides[current].querySelector('.speaker-notes');
  const text = notes ? notes.textContent.trim() : '(no notes)';
  document.getElementById('notes-panel-text').textContent = text;
  document.getElementById('notes-panel-slide').textContent =
    'Slide ' + (current + 1) + ' of ' + slides.length;
}

function openNotesPanel() {
  if (notesWin && !notesWin.closed) { notesWin.close(); notesWin = null; }
  panelOpen = true;
  document.getElementById('notes-panel').classList.add('open');
  document.getElementById('deck').classList.add('panel-open');
  document.body.classList.add('panel-open');
  updateNotesPanel();
}

function closeNotesPanel() {
  panelOpen = false;
  document.getElementById('notes-panel').classList.remove('open');
  document.getElementById('deck').classList.remove('panel-open');
  document.body.classList.remove('panel-open');
}

function openNotesWindow() {
  if (panelOpen) closeNotesPanel();
  if (notesWin && !notesWin.closed) { notesWin.focus(); return; }
  notesWin = window.open('', 'speaker_notes',
    'width=520,height=360,left=100,top=100');
  notesWin.document.write(`<!DOCTYPE html><html><head>
    <title>Speaker Notes</title><style>
    body{background:#111;color:#e0e0e0;
      font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',
      Helvetica,Arial,sans-serif;padding:28px 32px;margin:0;}
    #noteSlide{font-size:13px;text-transform:uppercase;
      letter-spacing:1.5px;color:var(--accent,#3B82F6);
      margin-bottom:16px;font-weight:600;}
    #noteText{font-size:20px;line-height:1.65;color:#d0d0d0;}
    .hint{position:fixed;bottom:16px;right:20px;
      font-size:12px;color:#555;}
    </style></head><body>
    <div id="noteSlide"></div>
    <div id="noteText"></div>
    <div class="hint">Navigate from main window</div>
  </body></html>`);
  notesWin.document.close();
  updateNotesWindow();
}

document.getElementById('notes-panel-close').addEventListener('click', closeNotesPanel);
```

Call both `updateNotesWindow()` and `updateNotesPanel()` inside `show()`. Bind keys in the `keydown` handler:

```js
if (e.key === 'n' || e.key === 'N') openNotesWindow();
if (e.key === 'b' || e.key === 'B') { if (panelOpen) closeNotesPanel(); else openNotesPanel(); }
```
