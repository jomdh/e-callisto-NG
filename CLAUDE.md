# CLAUDE.md — e-Callisto NG

Working agreement for the e-Callisto NG suite. The methodology is **inherited
from doncel.dev** (`../doncel.dev/CLAUDE.md`) and **right-sized to this project's
design choices**. Where the two differ, this file wins for e-Callisto NG.

## Project context

- **What it is:** a web-based solar radio spectrometer suite that runs **on a
  station** (a Debian/Raspbian computer, often a low-power Pi) and controls one or
  more instruments. Full design: **`e-Callisto-NG-DESIGN.md`** — the source of
  truth for *what* and *how*. Legacy analysis (the Windows/Linux predecessors we
  reverse-engineered) lives under `legacy/`.
- **Relationship to doncel.dev:** a **sibling at a different tier** — doncel is
  *analysis, server-hosted*; NG is *control, on the station*. They integrate later
  via **API + data + a shared design system**, not a UI merge. doncel is *not yet
  modular and will be refactored*; **don't mind its mess** — we take its
  methodology, not its current structure.
- **State:** greenfield, first deliverable. We are at **M0** (define contracts,
  then the record loop). No code yet — design first.
- **Don't auto-commit.** Commit only when explicitly asked. **No emojis** anywhere.

## Philosophy

A codebase **easy to understand and hard to misuse**. Before writing code, answer:

1. What does the existing code do, and why?
2. What problem am I solving, in full scope?
3. Why is this approach correct? What alternatives exist?
4. How will I verify correctness and avoid plausible regressions?

"I'm not sure" is never an acceptable answer to "why is X an improvement?"

## Workflow

**plan → understand → propose → implement → verify**, every task.

- **Plan first.** Check `docs/planning/ROADMAP.md` (seeded from design §18
  milestones) and the backlogs before starting. Work traces to a milestone.
- **Understand.** Read the area first; `git grep` for patterns; show existing
  similar code before proposing new code.
- **Propose before coding.** State your understanding, the change and why, how it
  fits existing patterns and the **contracts** (below), and what could break.
- **Implement in minimal, coherent commits** — one logical change each.
- **Verify** with the quality gate before committing.

## THE load-bearing principle: modularity & contracts

This is what makes e-Callisto NG different from doncel's current state. **Strict
separation of duties behind versioned contracts** (design §5a). Non-negotiable:

- **`core` depends on nothing concrete.** Imports flow **inward toward `core`**.
  No hardware, transport, format, or UI detail leaks into the core.
- **Everything variable is a plugin behind an interface:** Instrument Driver,
  Upload Transport, Output Writer, Schedule Rule, Renderer, Alert Channel, Auth
  Provider. Each has ≥1 implementation **plus a fake**.
- **Plugin contracts are semver-versioned.** Changing one is an **ADR + version
  bump**, never a silent break — third parties (incl. closed SDR/FPGA drivers)
  build against them (design §5b).
- **The instrument class hierarchy is invariant at the boundary:** heterodyne /
  SDR / SDR+FPGA all deliver **normalized spectra + capabilities** (design §5a);
  class-specifics (serial/EEPROM, host DSP, FPGA ingest) stay *inside* the driver.
- **The UI is one module behind the API contract** — swappable without touching
  the engine.

When a task touches a contract, treat it as architecturally significant: pause,
propose, and file an ADR.

## Architecture & layering

Monorepo, packages with one responsibility each; imports flow inward to `core`:

| Package | Responsibility | Naming (files / fns / classes) |
| -- | -- | -- |
| `core/` | domain models + **contracts/interfaces**, pure logic | plain nouns, `_result`, `_config` · `compute_*`, `build_*` · `*Result`, `*Config`, `*Error` |
| `drivers/*` | instrument drivers (Callisto first) | `*_driver` · `discover/connect/identify/configure/start/stop/stream` · `*Driver`, `*Capabilities` |
| `transports/*` | upload transports (FTP/SFTP…) | `*_transport` · `connect/put/verify` · `*Transport` |
| `writers/*` | output writers (legacy/standard/custom FITS) | `*_writer` · `write` · `*Writer` |
| `services/*` | acquisition, scheduler, uploader, jobs | `*_service`, `*_pipeline` · `run_*_job`, `start_*` · `*Parameters`, `*Result` |
| `api/` | FastAPI backend + **Jinja portal + static islands** | `portal_*`, REST verbs · `*Request`, `*Response` |

- **`*Config`** = static startup settings. **`*Parameters`** = runtime job inputs.
- Private helpers: `_<verb>_<noun>()`. Clear, greppable names. Don't duplicate
  correctness/access logic. Comments explain **why**, not what.

## Quality gate (run before every commit)

Same discipline as doncel, **single Python toolchain — no Node/SPA build**:

```
vulture → black --line-length 79 → flake8 --extend-ignore E203,W503 → ruff check → mypy (changed files) → pytest
```

- `snake_case` vars/functions/modules; `PascalCase` classes/Pydantic models.
- Max line 79; `logging` not `print`; type-hint all public functions.
- Imports: stdlib → third-party → local. US English (`normalize`, `color`).
- Every package **independently testable against its contract with fakes**
  (serial simulator, fake transport, fixed-clock ephemeris) — verify modules in
  isolation in CI. The **serial simulator** lets the whole stack run with no
  hardware.

### On-unit acceptance (milestone close)

The per-commit gate above runs hardware-free against fakes. Additionally, **a
milestone is not closed until verified on a real station** (a reference unit
with an actual Callisto), when one is available — not per sprint, once per
milestone. The on-unit pass installs/updates the suite on the unit, exercises
the milestone's behaviour against real hardware, and confirms the services
recover (restart/reboot). Record the result in the milestone's close log.

## UI: coherence without identical setup

- **Server-rendered Jinja portal + lightweight JS islands**, styled by the
  **shared, framework-agnostic M3 design system** (`material-design-system.css`,
  same as doncel) — themes **Nebula** (dark, default) / **Supernova** (light),
  DM Sans / Noto Sans / Material Icons. Consume it as a **versioned shared asset**;
  do not fork or hardcode colors/sizes — every visual property references a token.
- **Theme** via `data-theme` on `<html>`, persisted in `localStorage`, applied
  pre-render to avoid flash.
- **CSP `script-src 'nonce-…'`:** no inline `onclick`/`oninput`/etc. — use
  `addEventListener` in nonced `<script>` blocks; for dynamic content use
  `data-action` + event delegation.
- JS: `const`/`let` only. CSS: `em` not `px` for font-relative sizes.
- The **live waterfall is a WebGL/Canvas island over WebSocket** (GPU work runs in
  the operator's browser).

## Station invariants (load-bearing — from the design)

These encode the project's integrity and survivability; don't violate silently:

- **Raw ADC is the default** (§6b). Never auto-estimate dB; dB and SFU/Kelvin are
  opt-in. Never silently transform values; record which level produced a product.
- **Continuous NTP resync is paramount** (§12a). Timing gates recording; flag/
  pause on drift.
- **Degrade, don't die; never lose un-uploaded science data; isolate faults;
  always alert** (§14a). Acquisition is independent of the web app.
- **No default credentials**; admin created in the wizard. **.env is absolute** —
  never overwrite/commit; provide `.env.example`; read via Pydantic settings.
- **No hardcoded paths/routes/params** — use centralized config.

## Planning & decisions

- **Planning tree** under `docs/planning/`: `ROADMAP.md` (current state, seeded
  from design §18), `BUG_BACKLOG.md`, `FEATURE_BACKLOG.md`, and milestone plans.
  Right-sized for now: work is **traceable to a milestone**; adopt full
  sprint/logbook ceremony once there's a delivery cadence and a team.
- **ADRs** under `docs/architecture/decisions/ADR-NNN-*.md`, with `ADR_INDEX.md`
  updated in the **same commit**. File an ADR for: any **plugin-contract** change,
  schema changes, security-sensitive code, or a decision spanning milestones. Seed
  ADRs from the resolved decisions in design §19 (frontend, units, timing,
  failure policy, licensing-pending).
- **SNR discipline:** flag dead code as you go; sweep before milestone close.
  Verify with imports/tests before deleting, never just grep.
- **Protect stable features:** once a feature is validated, re-test on changes
  that could affect it; preserve user-facing contracts.

## When to pause and discuss

Stop and present options (don't silently pick) when a change: touches a **plugin
contract** or `core`; touches security (auth/tokens/permissions); changes the DB
schema; would modify >~10 files; has unclear performance impact; or affects a
validated/stable feature. Never remove features or change interaction patterns
without discussion. Don't preserve legacy code for backward-compat in the new
suite (legacy lives in `legacy/` for reference only).

## Differences from doncel.dev (deliberate)

| Aspect | doncel.dev | e-Callisto NG |
| -- | -- | -- |
| Tier | analysis, server | control, on-station (low-power) |
| Store | MongoDB | **SQLite** (single station) + filesystem for FITS |
| Frontend | Jinja portal + islands | **same pattern**, lighter; shared M3 design system |
| Modularity | not yet (to be refactored) | **modular-by-design from M0** |
| Methodology | full sprint/version lifecycle | inherited, **right-sized** until cadence exists |

## GitNexus

Adopt **once code exists** (greenfield now). When the codebase lands: index with
`npx gitnexus analyze`, then run **impact analysis before editing a symbol** and
**`detect_changes` before committing**, per the doncel convention. Until then,
apply the same discipline manually (read, `git grep`, propose, verify).

## Key commands

```bash
# Quality gate (in order, before every commit)
vulture src/ vulture_whitelist.py     # whitelist = intentional interface params
black --line-length 79 --check <pkg>/
flake8 --extend-ignore E203,W503 <pkg>/
ruff check <pkg>/ tests/
mypy <changed-files>
pytest                                  # full suite; or target a module

# Search & history (use constantly)
git grep "pattern"
git log --oneline -20 -- path/to/file
```
