# Sprint 0.1-M3-S012 -- frequency programs + overview-based generation

**Sprint Goal:** Define frequency programs -- by hand or auto-generated from a
spectral overview by picking the quietest channel per step.

**Full ID:** 0.1-M3-S012  **Milestone:** M3  **Branch:** ``0.1-dev``  **Status:** Planned.

## Decision

Pure generation logic (`services/freqgen.py`) ports the GenFrqPrg quiet-channel
idea; programs persist as a `FrequencyProgram` row with the channel list as JSON.
Wiring a program into a recording is a later refinement; this sprint delivers the
program as a first-class, generatable, CRUD-able object.

## Deliverables (5)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `services/freqgen.py` `generate_frequencies` | services | quiet (min-amp per bin) / even modes; pure |
| D2 | `FrequencyProgram` model | api | name + frequencies JSON + band + source |
| D3 | `routes/programs.py` CRUD + /generate | api | viewer read / operator write |
| D4 | tests | tests | quiet picks minimum; even spacing; CRUD + generate + RBAC |
| D5 | logbook | docs | -- |

## Acceptance Criteria

- [ ] Quiet mode picks the lowest-amplitude point per bin; even spaces centers.
- [ ] Create + generate + list programs; viewer blocked from writes.
- [ ] Gate green; tests pass.

## Out of Scope

Assigning a program to an instrument's recording; uploading a real overview file
(the generator takes points directly here). Scheduler is S013.
