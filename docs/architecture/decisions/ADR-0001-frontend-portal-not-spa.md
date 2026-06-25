# ADR-0001 — Frontend: server-rendered portal + JS islands, not a SPA

**Status:** Accepted

## Context

e-Callisto NG runs on a low-power station (often a Raspberry Pi) and must be
coherent with the sibling platform doncel.dev (analysis, server-hosted), which
uses a Jinja portal + JS islands + a framework-agnostic M3 design system. An
earlier draft specified a React/TS SPA.

## Decision

Use a **server-rendered Jinja portal (FastAPI) + lightweight JS islands**,
styled by the **shared, framework-agnostic M3 design system** (Nebula/Supernova
themes) consumed as a versioned asset. The live waterfall is a client-side
WebGL/Canvas island over WebSocket. **No React/SPA toolchain.**

## Rationale

- **Coherence is decoupled from stack** — the M3 stylesheet is pure CSS tokens,
  so the portal matches doncel without an identical setup.
- **At runtime on the Pi the options are ~equal** — the heavy live rendering is
  a client-side island regardless; station concurrency is tiny.
- **Integrity wins it** — one Python toolchain, one dependency tree, one quality
  gate; smallest surface for a near-autonomous appliance. React adds a second
  toolchain whose complexity a station console never repays.
- **Not a one-way door** — the UI is one module behind the REST/WS API contract
  and can be swapped later.

## Consequences

- Frontend lives in `api/` (Jinja templates + static islands); no Node build.
- Adopt doncel's CSP/nonce + `data-action` event-delegation rules and `em`-based
  sizing.
- Revisit only if the console grows into a large, app-like interface with heavy
  client state.

Reference: DESIGN sections 4, 4a, 8.
