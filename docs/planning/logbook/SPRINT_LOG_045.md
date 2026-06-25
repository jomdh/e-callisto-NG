# Sprint 0.6-M19-S045 -- component polish (M19 close)

**Status:** Completed (2026-06-25)  **Branch:** `0.6-dev` -> merged to `main`

## Goal / Met?
Visual component polish. **Met** -- buttons use the M3 filled/text variants and
headings/cards have a consistent treatment.

## Actions
- Mapped every button: `btn` -> `btn-filled`, `btn btn-ghost` -> `btn-text`, in
  templates and the JS islands (console row-actions/submit, tools, viewer,
  settings).
- portal.css: bordered page `h2`, `h3`, card bottom-spacing, compact `.btn-text`
  inside console tables.

## Verification
Gate green: vulture/black/ruff/flake8/mypy/pytest (**180 passed**).

## Milestone M19 -- complete
S044-S045. The portal now wears doncel's visual language: a left vertical sidebar
with section icons (Operations / Configure / Tools / Distribution / Admin),
grouped labels + dividers, a nebula/supernova theme toggle, collapse + mobile
drawer, M3 buttons and cards -- colours from our Nebula/Supernova tokens.
Version -> v0.6.0; merged to main.

## Lessons
- doncel's `.btn-filled`/`.btn-text` are self-contained, so the swap was a pure
  class rename -- no structural change to any button.

## Tag
`v0.6.0` at the M19-complete commit; merged to main.
