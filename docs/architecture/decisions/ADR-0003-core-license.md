# ADR-0003 — Core license: GPLv3 vs AGPLv3

**Status:** Accepted — **AGPLv3** (owner decision, 2026-06-25)

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

**AGPLv3** for the core + web app. The suite is served over the network, so AGPL
ensures hosted forks (e.g. an institution running a modified portal) contribute
improvements back — the SaaS loophole GPLv3 leaves open. Continuity with the
GPLv3 legacy daemon is preserved (AGPLv3 is GPLv3-compatible for combination).

**Plugin boundary (unchanged, §5b):** drivers/transports/writers run across the
documented IPC/contract boundary (the acquisition driver is a separate process),
so a third party may ship a **closed-source** driver (e.g. a proprietary FPGA
SDR) without it becoming a derivative work of the AGPL core. Plugin contracts
stay semver-versioned. This is the load-bearing reason the boundary is a process
+ versioned contract, not an in-process import.

**Contributions:** a **DCO** (Developer Certificate of Origin, sign-off line) is
required; no CLA. Lightweight, keeps copyright with contributors.

**Application (M25):** add `LICENSE` (AGPLv3 text), a short SPDX header
(`SPDX-License-Identifier: AGPL-3.0-or-later`) to source files, a `NOTICE`/README
license section, and a plugin-governance note that the contract boundary permits
independently-licensed drivers.

Reference: DESIGN sections 5b, 19.
