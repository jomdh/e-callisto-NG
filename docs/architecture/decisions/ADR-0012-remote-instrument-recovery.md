# ADR-0012 — Remote instrument recovery: liveness escalation to a privileged power-cycle

**Status:** Accepted  **Date:** 2026-06-27  **Milestone:** M38

## Context

ADR-0010 contains instrument instability **inside the driver**: a no-data
timeout drives a bounded `reset/init/start`, and when the budget is exhausted the
driver raises `FatalInstrumentError`, which the engine (`recorder`/`scheduler`)
answers by tearing the driver down and rebuilding it. That is the right seam —
but every step of it is **software**. A rebuild reopens the *same enumerated
device*. It cannot help a receiver that has stopped delivering data while staying
enumerated.

That failure mode is real and was observed on the reference Pi 5 station: the
Callisto's PL2303 stayed enumerated (`/dev/ttyUSB0` present, opens cleanly, the
acquire daemon holding the fd), yet **zero frames and zero FITS files for ~2
hours** while the recorder state read `recording`. A full `ecallisto-acquire`
restart — which re-runs the entire driver init — did not revive it. Neither would
a reboot: none of these **cut VBUS**. The device needs the electrical equivalent
of unplug/replug. For a station that sits **alone in a remote location with no
expected visits**, "wait for a site visit" is not an acceptable recovery.

Two distinct gaps surface this class of fault:

1. **Detection is by proxy, not measurement.** `RECORDING` is *aspirational* —
   it is set when the record loop starts, not while frames flow. There is no
   `last_frame_at` (ADR-0010 named it and deferred it, line 94). Each consumer
   infers health differently: the recorder checks thread `is_alive()`, diagnostics
   checks newest-FITS mtime, the live UI shows a blank canvas. No single liveness
   truth, so a mute-but-enumerated device reads as healthy everywhere.

2. **Recovery has no privileged lever.** The station user is intentionally
   minimal (least privilege): it may `sudo systemctl restart` the two services and
   nothing else. A true USB power-cycle (`uhubctl`), `usbreset`, or driver
   unbind/rebind is root. There is no audited path from "device is mute" to "cut
   power to its port" — and physical access is off the table.

## Decision

Make liveness a **first-class, measured signal**, and extend recovery **beyond
the driver to a privileged host action** via the existing ADR-0008 host-hook —
not a new parallel helper.

### 1. First-class liveness (`last_frame_at`)

Add a per-instrument **`last_frame_at`** heartbeat — the timestamp ADR-0010
deferred. The recorder stamps it on every published frame (the existing
`on_frame` path that already feeds the live bridge); it is persisted on
`RecorderRuntime` alongside `state`. `RECORDING` stops being aspirational:

```
STALLED  ⇔  state == recording  AND  now - last_frame_at > stall_bound
```

`stall_bound` is relative to sweep cadence (like the driver's no-data timeout,
but at the **engine** level and longer — the driver gets first crack at
self-heal). STALLED is one truth, read by **every** consumer: the dashboard tile
(a clear "not responding", not a blank waterfall), the live WebSocket (emits a
status frame so the browser shows the condition instead of an empty canvas),
diagnostics (replaces the file-mtime proxy as the primary signal), and alerts.

### 2. Recovery escalates to the audited host-hook (ADR-0008)

When the driver's own self-heal is exhausted (`FatalInstrumentError`) **and** a
rebuild does not restore frames, the remaining lever is a privileged
**escalation ladder**, run by the host-hook:

```
usbreset (USBDEVFS_RESET)  →  driver unbind/rebind  →  uhubctl per-port VBUS power-cycle  →  reboot
```

The hook resolves the instrument's **USB topology from its serial device path**
(`/dev/ttyUSB* → sysfs → hub location + port`) so it power-cycles *exactly* that
port. It runs as root through a **single narrow NOPASSWD sudoers entry** for the
one hook path, installed by `scripts/install.sh`. The web/acquire processes stay
unprivileged; privilege lives only in the audited hook (ADR-0006), reached via
the closed verb set. This is an **amendment to ADR-0008**: the hook ships a real
script, and the per-instrument `reconnect`/`recover` verb means "walk the
recovery ladder for this instrument," up to but not including reboot (reboot
stays its own verb).

### 3. Trigger: manual always; automated opt-in and bounded

- **Manual, always available:** a **Recover device** action in the instrument
  workspace (`POST /api/v1/instruments/{id}/reconnect`, already wired and
  audited) lets an operator power-cycle from anywhere a browser reaches the
  portal. This works the moment the hook + sudoers are installed.
- **Automated, opt-in:** the acquire watchdog invokes the hook when STALLED
  persists past the driver's self-heal budget. Gated by a new
  **`auto_recover` setting (default `false`)** and **bounded** by a recovery
  budget per time window — when the budget is spent it **stops and alerts**
  rather than looping power-cycles forever.

**Safe out of the box:** with no `host_hook` configured and `auto_recover` off,
behaviour is unchanged — detection still improves (STALLED is surfaced), but
nothing privileged runs. A station opts into automated recovery deliberately.

## Consequences

- **One liveness truth.** Dashboard, live WS, diagnostics, and alerts all read
  `last_frame_at`/STALLED instead of three independent fragile proxies. A mute
  device can no longer read as healthy.
- **Recovery without physical access.** The common wedge is fixable remotely —
  by an operator clicking *Recover device*, or automatically on an opted-in
  station. The privilege surface stays the closed verb set + the hook's own
  narrow sudoers; the engine never gains hardware privilege.
- **The seam holds.** The engine knows only *frames* and a *recover verb*; the
  hook alone knows `uhubctl`, sysfs topology, and unbind/rebind. Hardware
  specifics do not leak above the host-hook.
- **No driver-contract change.** ADR-0010 is untouched; this is precisely the
  engine-side heavy-recovery escalation it deferred. ADR-0008's verb set is
  amended (a real hook + recover semantics), recorded here.
- **Testable without hardware.** The fake hook already asserts verb/args + audit;
  a fault-injecting fake driver that goes mute drives STALLED detection and the
  opt-in auto-recover trigger in CI. The hook script's topology resolution is
  unit-tested against a fixture sysfs layout.
- **Honest about limits.** If a device hangs off a hub without per-port power
  switching, `uhubctl` cannot cycle it; the ladder falls through to `reboot` and,
  failing that, **alerts** — the operator manual (`OPERATIONS.md` §5) documents
  this boundary. The feature reduces, but cannot in every topology eliminate, the
  need for a last-resort human.

## Note on rollout

Detection (§1) and the manual lever (§2–3) ship first and are deployable to the
reference station immediately; automated triggering (§3) lands behind
`auto_recover` once the hook is validated on real hardware (uhubctl confirmed to
power-cycle the Callisto's port). `OPERATIONS.md` §5 is updated from "manual
procedure" to "automated, with manual override" as each half lands.
