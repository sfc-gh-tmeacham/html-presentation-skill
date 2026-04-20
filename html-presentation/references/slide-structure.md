# Slide Structure

Every deck follows this flow:

| Slide | Purpose | Content |
|-------|---------|---------|
| **1. Title** | Set the stage | Big title, subtitle, your name or brand |
| **Agenda** | Orient the audience | Numbered card grid of 3–6 thematic sections (not counted toward slide max) |
| **BLUF** | Bottom Line Up Front | 3-card summary stating the key takeaways upfront (not counted toward slide max) |
| **2. Setup** | Frame the problem or context | Why this matters, what the audience will learn |
| **3-8. Core Content** | Deliver the meat | One idea per slide, each with a visual component |
| **9. Evidence** | Prove your point | Stats, quotes, case studies, examples |
| **10. Takeaway** | Land the message | Summary, call to action, next steps |

Adjust core content slides by topic complexity. Simple: 5–7 total. Moderate: 10–15. Deep-dive: 20–25. Never exceed 30.

**Executive Deck Structure (exec_mode):** When `exec_mode` true, follow exec deck plan in Step 2 (BLUF-first, 7-slide cap, no Agenda). Cap at **7 content slides**.

**Presenter Slide (optional):** If requested, include immediately after Title slide (before Agenda). Does NOT count toward slide max.

**Presenter slide visual rules:** See **Presenter Slide** in `references/visual-components.md` for exact layout, headshot sizing, CSS values for 1, 2, and 3+ presenter layouts. All headshots MUST be circularly cropped (`border-radius: 50%; object-fit: cover; equal width/height`). Max 9 presenters — `insert_presenter.py` errors if exceeded.

For HTML patterns, see **Presenter Slide** in `references/visual-components.md`.

**Agenda Slide (mandatory, except exec decks):** Every non-exec deck MUST include Agenda slide immediately after Title (or after Presenter slide if present). Exec decks skip entirely. Does NOT count toward slide max. List 3–6 thematic sections (not every individual slide).

**BLUF Slide (mandatory for non-exec decks):** Every non-exec deck MUST include BLUF slide immediately after Agenda. Does NOT count toward slide max. In exec mode, no standalone BLUF — embedded in Slide 2 (Executive Summary). Use card layout (2–4 cards), each stating one key takeaway as concrete outcome. Each card: headline (bold, white) + 1–2 sentence elaboration (secondary color). Relevant Material Icon per card (accent-colored). Eyebrow `h3` = short contextually appropriate label.

**Agenda visual rules:**
- **Numbered card grid** (2 or 3 columns), one card per section
- Each card: Material Icon (accent-colored, `clamp(1.5rem, 2.5vw, 2rem)`), bold section title (`clamp(0.9rem, 1.4vw, 1.2rem)` white), one-line descriptor (`clamp(0.75rem, 1.1vw, 1rem)` secondary color)
- Cards use standard card style (`background: var(--card)`, `border: 1px solid var(--border)`, `border-radius: 12-16px`, `padding: 20-24px`)
- Add subtle accent-colored number or left border to reinforce sequence
- Stagger card animations for sequential reveal
- Heading = small uppercase `h3` (e.g., "Agenda", "What We'll Cover", "Today's Session") with accent color, NOT large `h2`
- Prefer card grid over plain text list. Icon list acceptable for short agendas (3 items or fewer).

For full HTML pattern, see **Agenda** in `references/visual-components.md`.
