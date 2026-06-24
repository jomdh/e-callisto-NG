# ADR-0003 — Core license: GPLv3 vs AGPLv3

**Status:** Open (awaiting owner decision)

## Context

Modularity and a third-party plugin ecosystem are first-class goals. The legacy
Linux daemon is GPLv3. e-Callisto NG is a network-served application.

## Options

- **GPLv3** — continuity with the legacy daemon; standard strong copyleft.
- **AGPLv3** — closes the network/SaaS loophole so hosted improvements flow back
  (relevant since the suite is served over the network).

## Independent of the choice

Drivers/transports/etc. run across **documented IPC/contract boundaries** (the
acquisition driver is a separate process), so a vendor can ship a **closed-source
driver** (e.g. for a proprietary FPGA SDR) without it being a derivative work of
a copyleft core. Plugin contracts are semver-versioned.

## Decision

**Pending.** Also open: whether a CLA/DCO is required for contributions.

Reference: DESIGN sections 5b, 19.
