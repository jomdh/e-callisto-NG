# ADR-0011 -- Operations-room IA: per-instrument workspace hub + station spine

**Status:** Accepted  **Date:** 2026-06-27  **Milestone:** M37

## Context

The portal grew feature-by-feature (M0-M36) into a function-grouped sidebar --
Operations / Configure / Tools / Distribution / Administration, ~20 links.
Coverage matches DESIGN §8 (verified 2026-06-27), but the **information
architecture tells no story**: the **instrument** -- the thing an operator
actually reasons about -- is one link among twenty, and the operations *of one
instrument* are scattered across four different sidebar groups (its Schedule
under Configure, its Programs under Configure, its Bench under Tools, its Live
reachable only from the Dashboard). To do everything for one receiver the
operator hops across the whole menu.

The product intent is a **storytelling** one: the portal is the station's
**operations room**, and **instruments are central** inside it. M25 already
began the instrument-centric move (the per-instrument *device console*), but the
rest of an instrument's operations stayed in function pages -- a half-finished,
inconsistent model.

Two candidate models were on the table:

- **(A) Matroska / nest:** each instrument has one dedicated page that folds in
  all of its operations and configs.
- **(B) Function-centric / attach:** operations are station-level sections and
  instruments are attached/filtered within them (today's layout).

Research into analogous domains (`docs/planning/research/` IA brief, 2026-06-27)
-- High-Performance HMI / **ISA-101** Level 1-4 display hierarchy; observatory
controls (**TANGO/EPICS/INDI** device-oriented middleware + task-oriented
operator tools); device-fleet platforms (**Home Assistant** Device page, **AWS
IoT** Thing, **SolarWinds** Node Details, **Grafana** host + cross-cutting
dashboards); and IA theory (**OOUX**, master-detail, faceted navigation) -- all
converge on the **same hybrid** and the **same deciding heuristic**.

The key insight that unblocks the decision: **data-model ownership and
navigation structure are independent axes.** "The instrument owns its schedule"
(data) does not entail "all navigation nests inside the instrument" (nav). A and
B each conflate the two.

## Decision

Adopt the hybrid the analog domains converge on. Two complementary structures
over one object-canonical data model.

### 1. Data model -- the Instrument is the canonical owning object (OOUX)

Schedules, frequency programs, calibration sets, and bench state are **owned by /
scoped to a single instrument**. This is already true in `api/models.py`; this
ADR makes it an **invariant**: no per-instrument operation floats free of an
instrument. (Genuinely station-wide objects -- upload targets, users, access
config, time policy -- are owned by the station, not an instrument.)

### 2. Navigation -- operations-room overview + per-instrument workspace + spine

- **Operations Room (Level 1).** The Dashboard is the room: all instruments as
  central, live status tiles -- recording state, mini-waterfall, next action,
  alerts -- with drill-in.
- **Per-instrument Workspace (the hub; Level 2/3 faceplate).** Drilling into an
  instrument opens *its* workspace: **Live, Schedule, Programs, Calibration,
  Bench, Config**, plus a snapshot of **its recent data and upload status** --
  all scoped to that instrument. This is where option-A nesting applies, and it
  finishes the M25 console move.
- **Station spine.** The genuinely cross-instrument / host-level views stay
  top-level: **Data archive, Distribution queue, Health & alerts, Time,
  Diagnostics, Fleet**, and **Admin** (Access, Users, Audit, Settings, Import).

### 3. The routing heuristic (the contract for where any future screen goes)

> **Single-instrument context -> the instrument workspace. Cross-instrument
> aggregate or station/host concern -> the station spine, with the instrument as
> a filter where relevant.**

Test: *"show me everything about this instrument"* -> workspace. *"show me X
across the station"* -> spine. Every new screen is routed by this rule.

### 4. The Workspace is a defined shell, class-gated by capabilities

The per-instrument workspace is a **tabbed shell** over the instrument route. Its
tabs are gated by the instrument's **capabilities** (DESIGN §5a): a heterodyne
Callisto shows the EEPROM/relay Bench tab; an SDR shows its own bench surface and
no EEPROM tab. New instrument classes fill the same shell -- consistent with the
driver/capabilities contract. This is a **UI-layer contract**, not a plugin
contract: it does **not** bump `CONTRACT_VERSION`.

### 5. Function pages become station views; the per-instrument editor moves in

The editing of an instrument's schedule/program/calibration becomes
**single-sourced in its workspace**. The former function pages survive as
**station-level read/aggregate views** (e.g. a cross-instrument schedule
timeline, the upload queue, the data archive) -- not deleted, re-scoped. Old
routes **redirect with an instrument filter** (`/portal/manage/schedules` ->
workspace or `?instrument=N`) so no link or bookmark is orphaned.

## Consequences

- **Sidebar restructures** from five function groups to three:
  **Operations Room** (Dashboard + instrument drill-in) / **Station** (Data,
  Distribution, Health, Time, Diagnostics, Fleet) / **Admin**.
- **`instrument_detail.html` becomes the Workspace shell**; today's scattered
  Schedules / Programs / Calibration / Bench / Live consolidate into its
  instrument-scoped tabs.
- **The standalone Planning page resolves** (the open question from 2026-06-27):
  its config role already folded into the schedule editor (M35); the page becomes
  a station-coordinate **Ephemeris** explorer in the spine, or retires. Decided in
  the M37 plan, not here.
- **No data migration.** Models are already instrument-owned; this is
  presentation + routing + an invariant. Existing API endpoints keep working
  (scoped/redirected).
- **ADR-0001 holds.** Workspace tabs are server-rendered + nonced JS islands with
  `data-action` delegation; no SPA, no inline handlers. Builds on M19 (visual
  shell) and M25 (device console); supersedes nothing.
- **Risk: a large UI change can regress validated flows.** Mitigation: phase the
  move tab-by-tab; keep every function endpoint reachable (redirect/scope) so
  nothing is orphaned; close on **on-unit acceptance** (CLAUDE.md) -- the reorg is
  verified on the reference station before milestone close.

## Note on location

Ships with the `docs/architecture/` subtree, alongside ADR-0001 -- it is the
frontend-shape companion to the portal-not-SPA decision and orients any
contributor working on the UI module.
