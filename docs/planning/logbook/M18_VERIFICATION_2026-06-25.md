# M18 (Wizard completeness) -- verification pass, 2026-06-25

Methodology re-verification of milestone **M18** (closed at v0.5.3 / sprint S043)
against its acceptance criteria, run live this session. No code changed -- M18 was
already complete; this is the **understand -> verify** evidence.

## Acceptance criteria vs evidence

| Criterion (M18 plan) | Result | Evidence (this session) |
| -- | -- | -- |
| D1 multi-step resumable wizard | PASS | Fresh `/` -> `303 /wizard`; steps admin -> station -> coordinates -> instrument -> review (Step 5 of 5); a **new client mid-flow resumed at Step 3 of 5** (server-side `wizard_state`); finish -> `303 /portal`; after setup `/` -> `/portal` (no longer forced to the wizard). |
| D2 map picker for coordinates | PASS | The coordinates step renders `map-canvas` (offline equirectangular picker, M23/S052). |
| D3 clone/import branch | PASS | `wizard.py` `callisto.cfg` paste pre-fills station/instrument; `import.html` present; `POST /api/v1/import` (migrate router) provisions from a legacy station. |
| D4 wizard steps = persistent editors | PASS | After the run the admin user, station + coordinates (VERIFY-RPI, 47.1, 8.2), and instrument (Callisto-1) all persisted; the same forms back the management console. |
| Gate green; tag v0.5.3; merge to main | PASS | 7 wizard/map tests pass; `git tag --merged main` lists `v0.5.3`; `git branch --contains v0.5.3` includes `main`; `SPRINT_LOG_043.md` records the M18 close. |

## Note on scope
The shipped wizard is 5 steps (admin, station, coordinates, instrument, review).
The M18 plan's D1 table listed program/schedule/access as additional steps; those
were deliberately right-sized to the post-setup management console (D4: "one set
of screens, two entry points") and accepted at the v0.5.3 close. Not reopened.

## Conclusion
M18 is complete and remains valid at the current head (v0.8.1). Verified via the
methodology in-session; nothing to implement.
