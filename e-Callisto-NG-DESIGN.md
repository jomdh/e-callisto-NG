# e-Callisto NG — Web-based Solar Radio Spectrometer Suite

**Design specification, v0.1 (foundational).**
Name: **e-Callisto NG** ("next generation"). Target: a single **Debian/Raspbian**
computer (a Raspberry Pi *or* a larger x86/ARM machine) driving one or more
Callisto receivers, fully operated from a web browser.

This document defines *what* the suite is and *how* it is structured. It is a
clean-sheet design — it reuses the **domain knowledge** distilled in
`sources/WINDOWS_FUNCTIONALITY.md` and `sources/LINUX_FUNCTIONALITY.md` (the
serial protocol, FITS format, frequency-program logic, scheduling, calibration,
upload) but carries **no code or technology constraints** from them.

---

## 1. Vision & goals

A station operator opens a browser, points it at the station, logs in, and does
*everything* from there: set up the instrument, watch the live spectrogram,
manage frequency programs and schedules, browse and download data, push it to the
central archive, and run hardware diagnostics — with no Windows, no desktop GUI,
no manual config-file editing, and no per-tool app sprawl.

Design goals, in priority order:

1. **Web-first & remote.** 100% of functionality is reachable over the network
   through one authenticated web app. No SSH or file editing required for normal
   operation.
2. **Zero-to-observing in minutes.** A guided install wizard takes a fresh
   machine to a recording station without touching a terminal.
3. **Unattended reliability.** Once configured it records, schedules, and uploads
   on its own, survives reboots/power loss, and self-heals on hardware glitches.
4. **Scientifically faithful.** Same data products as the legacy system (8-bit
   time×frequency FITS, light curves, spectral overviews) with correct UTC
   timing, plus optional calibration — fully interoperable with the existing
   e-Callisto archive.
5. **Observable & safe.** Health dashboard, alerts, role-based remote login,
   audit trail, encrypted transport.
6. **Modular & extensible by design.** *Paramount.* Strict separation of duties
   and well-bounded modules behind versioned contracts, so the code can be
   improved part-by-part and the **network can grow with new instruments — both
   more instances and entirely new instrument types — without touching the
   core** (see §5a). Clean REST + WebSocket API for scripting/integration.

Non-goals (v1): offline scientific *analysis* beyond quicklook (burst
classification, type II/III analysis) — these stay in downstream tools; the suite
focuses on **acquisition, control, management, and distribution**.

---

## 2. Domain model, scope & assumptions

### 2.1 Terminology

The suite is built around a three-level hierarchy. This vocabulary is used
consistently throughout the document, the data model, the API, and the UI:

- **Observatory** — the owning organization (a university, research institute,
  amateur group, etc. — **not limited to universities**). An observatory owns
  **one or more stations**. This is where multi-station ("fleet") oversight lives.
- **Station** — **the computer**: any Debian/Raspbian machine (a Raspberry Pi or
  a larger x86/ARM box) running e-Callisto NG. A station **controls one or more
  instruments**. *This suite installs on, and primarily manages, a single
  station.* Station settings, remote access, users, storage, and updates are all
  station-scoped. (More instruments ⇒ a beefier station — see §3.)
- **Instrument** — a **Callisto receiver** (a serial device) controlled by a
  station. Recording, frequency programs, schedules, calibration, and data
  products are all **instrument-scoped**.

```
Observatory  (the organization — university, institute, amateur group, …)
└── Station (Debian/Raspbian computer — Pi or larger)   ← v1 unit of deployment
    ├── Instrument A (receiver on /dev/serial/...)
    └── Instrument B (receiver on /dev/serial/...)       ← pairs/sets are normal
```

**v1 scope = one station and its instruments.** The Observatory/fleet layer
(overseeing *several stations*) is a later phase; the data model and API are kept
**fleet-ready** so it layers on without rework.

### 2.2 Scope & assumptions

- **Multi-instrument is the common case.** Most stations are run by
  **institutions (commonly universities, but also other observatories) and
  control instruments in pairs or sets** (e.g. two receivers covering different
  bands/polarizations, or several at one site). So **a station drives multiple
  instruments** as the *normal* configuration, not an edge case. **Multi-instrument
  is always the model** — the data model, UI, scheduler, and uploader are all
  instrument-scoped — and a **single-instrument** station is just the N=1 case
  (one instrument in the list). There is **no single-vs-multi mode to pick**; you
  add one instrument or several, the same way.
- **Observatory context.** Observatories value **standardization across their
  stations**: config export/import (provision a second station from the first),
  bulk
  defaults, and a path toward central **fleet** oversight of multiple stations
  (kept fleet-*ready* even though it is a later phase).
- **Dynamic IP is the norm.** Most stations sit behind NAT on a dynamic IP, so
  remote access cannot assume a static public address (see §10).
- **Intermittent internet.** The station may be behind a slow/flaky link (the legacy
  notes mention satellite). Everything works offline; uploads queue and retry.
- **Operators are scientists/amateurs, not sysadmins.** UX must hide Linux.
- **Hardware** is the existing Callisto receiver (CD1316-class tuner) on a
  USB/serial port at 115200 baud, firmware ≥1.7 (1.8 preferred); the suite probes
  and adapts. Calibrated front-ends optional.

---

## 3. Target environment

**The station is any Debian-family Linux computer — not limited to a Raspberry
Pi.** A Pi is the reference low-cost option; an x86-64 mini-PC or a larger server
is equally valid (and preferable for instrument-dense stations).

- **OS (first-class):** **Debian** and **Raspberry Pi OS (Raspbian)** are the two
  supported reference platforms — same `.deb`, both **arm64 and amd64**. Ubuntu /
  other Debian derivatives work as a bonus, not a target.
- **Hardware:** anything that runs Debian/Raspbian with enough USB-serial ports
  for its instruments — Raspberry Pi 4/5 (Pi 3B+ as floor for 1 instrument), Intel
  N100-class mini-PCs, NUCs, or rack servers.
- **Sizing scales with instrument count *and class* (§5a).** For **class-1
  heterodyne** and **class-3 SDR+FPGA**, per-instrument host data/CPU is tiny
  (≈KB/s, light), so what grows is just the count of **acquisition daemons + live
  streams + quicklook/upload jobs**. **Class-2 SDR (host DSP)** is the exception:
  it does **wideband FFT/channelization on the host**, which can need real CPU
  (SIMD) or a GPU and high USB3/Ethernet bandwidth. Rough guidance:
  | Workload | Reference station | RAM | Notes |
  |---|---|---|---|
  | 1 instrument (class 1/3) | Pi 3B+/4 | 1–2 GB | minimal |
  | 2 (typical pair, class 1/3) | Pi 4/5 | 2–4 GB | the common case |
  | 3–6 (class 1/3) | Pi 5 or mini-PC | 4–8 GB | mini-PC if many live viewers |
  | any **class-2 SDR (host DSP)** | x86 mini-PC / server (± GPU) | 8 GB+ | DSP-bound, not count-bound |
  | 6+ mixed | x86 mini-PC / server | 8 GB+ | size to the heaviest driver hosted |
  The **one-process-per-instrument** design (each daemon isolated, §5) lets a
  single station mix a light heterodyne and a heavy SDR; **size the box to the
  heaviest driver it hosts**, and the same software spans a Pi to a multi-core
  server unchanged.
- **Constraints differ by class:** for class 1/3 the limits are **storage and
  clock accuracy**, not CPU; for class-2 SDR, **host DSP throughput and link
  bandwidth** join them. Provision disk for retention × instruments; prefer
  SSD/USB-SSD over SD cards on busy stations.
- **Station connectivity:** Ethernet or Wi-Fi for the operator/web + uploads.
- **Device connection medium varies by class — the platform supports all three:**
  | Class | Instrument link | Identified by |
  |---|---|---|
  | 1 Heterodyne (e-Callisto) | **COM-over-USB serial** (USB-serial adapter, per legacy code) | `/dev/serial/by-id/*` symlink |
  | 2 SDR dongle | **USB** (bulk, via SoapySDR/librtlsdr-class libs) | USB bus/serial / device id |
  | 3 SDR + FPGA | **USB *or* Ethernet** (network-attached appliance) | USB id, or **host:port / mDNS** |
  Each instance is pinned to a **stable identifier** (serial `by-id`, USB device
  id, or IP/hostname) so instruments never swap on reboot. A network-attached
  class-3 device is addressed by `host:port`, not a `/dev` node — the connection
  layer must not assume a local device file.
- **Time:** NTP/chrony mandatory and **continuously resynced** — not a one-time
  boot step. Regular, ongoing synchronization is **paramount** because FITS
  timestamps are scientific data; the suite continuously monitors offset/drift and
  flags or refuses recording when it exceeds threshold (full model in §12a).

---

## 4. Technology stack (decisions + rationale)

These are concrete choices; alternatives noted. The guiding principle: **one
cohesive stack a small scientific community can maintain**, with hard real-time
isolated into a small, robust piece.

| Layer | Choice | Why | Alternatives considered |
|---|---|---|---|
| **Acquisition daemon** | **Python 3.12** service using `pyserial`, one dedicated process per receiver | Data rate is tiny; Python keeps one language for the whole project and lowers the contribution barrier for scientists. Isolated as its own supervised process so a stall can't take down the web app. | Rust/Go/C daemon (more robust real-time, higher barrier) — kept as an escape hatch if timing ever bites. |
| **Backend API** | **Python + FastAPI** (ASGI, `uvicorn`) | Async, first-class WebSockets, automatic OpenAPI docs, Pydantic validation. Pairs with the science stack. | Node/NestJS, Go/Fiber. |
| **Science/data** | **astropy** (FITS I/O & WCS), **NumPy**, **skyfield**/**astropy** (sun rise/set/transit) | Battle-tested FITS and ephemeris — replaces hand-rolled MEEUS and the Emacs-calendar hack. | `cfitsio` bindings; custom ephemeris. |
| **Metadata store** | **SQLite** (WAL mode) via SQLModel/SQLAlchemy | Single-file, zero-admin, perfect for a single station. Holds config, users, file index, schedules, jobs, audit. | Postgres (overkill for one station). |
| **Bulk data** | **Filesystem** (FITS, PNG quicklooks, overviews, light curves) under `/var/lib/callisto`, indexed in SQLite | FITS files are the portable science product; never locked into a DB. | Object store (not on a Pi). |
| **Frontend** | **Server-rendered Jinja2 portal (FastAPI) + lightweight JS islands** (vanilla / Alpine-or-htmx-class), styled by the **shared M3 design system** | **Single Python stack — no Node/SPA toolchain** on a low-power station: smallest footprint, one dependency tree, one quality gate. The heavy live rendering is still a client-side island (below), so nothing is lost. Coherent with doncel.dev's portal (same pattern + design system) without an identical setup. | React/TS SPA (rejected: second toolchain, unrepaid complexity for a station console — see §4a). |
| **Design system (UI coherence)** | **Shared, framework-agnostic M3 stylesheet** (`material-design-system.css`) — Nebula (dark) / Supernova (light) themes, DM Sans / Noto Sans / Material Icons; consumed as a versioned shared asset | **Visual coherence with doncel.dev is decoupled from the rendering stack** — the design system is pure CSS tokens, so the station portal looks identical without sharing doncel's full setup. | Bespoke CSS (loses coherence). |
| **Live spectrogram** | **WebSocket** binary frames → **Canvas/WebGL** waterfall **JS island**; small charting lib (e.g. uPlot) for line plots | GPU rendering offloads to the operator's browser regardless of page stack; doncel's WebGL globe proves the islands pattern handles real-time. | Plotly (heavier), server-rendered PNG (not live). |
| **Reverse proxy / TLS** | **Caddy** (auto self-signed + optional Let's Encrypt) | One-line HTTPS, automatic certs if a domain exists, simple config. | nginx + certbot (more steps). |
| **Process supervision** | **systemd** units (web, per-receiver daemon, scheduler, uploader) | Native, reliable restarts, boot integration, journald logs. | supervisord, Docker. |
| **Packaging** | **`.deb` package** + first-boot wizard; optional **prebuilt SD image** | Native apt install/upgrade; image for non-technical users. | Snap/Flatpak, raw script. |
| **Background jobs** | In-process async task runner + systemd timers (no external broker) | Keeps footprint tiny; jobs are few (uploads, quicklooks, schedule recompute). | Celery+Redis (too heavy for a Pi). |

> Containerization (Docker) is **optional/secondary**: serial-device + systemd +
> low-overhead goals favor a native install on the station. A Compose file can be
> provided for development.

### 4a. Frontend decision — why server-rendered portal, not a SPA

e-Callisto NG and **doncel.dev are different tiers**: doncel is **analysis,
server-hosted**; NG is **control, on a low-power station**. The frontend is chosen
for **hardware efficiency and project integrity**, with visual coherence handled
separately:

- **Coherence is decoupled from stack.** doncel's M3 design system is *explicitly
  framework-agnostic* (pure CSS tokens). NG imports the **same stylesheet/themes**
  as a shared versioned asset → pixel-coherent with doncel **without** an identical
  setup. So the choice is purely efficiency + integrity.
- **At runtime on the Pi, stacks are roughly equal** — the demanding piece (the
  live waterfall) is a **client-side WebGL island** either way, offloaded to the
  operator's browser GPU. Station concurrency is tiny (1–2 operators); page-render
  cost is negligible.
- **Integrity wins it.** A Jinja portal keeps **one language, one toolchain, one
  dependency tree, one quality gate** (reuse doncel's `black/flake8/ruff/mypy/
  pytest/vulture` verbatim) — smallest attack/maintenance surface, best fit for a
  *solid, near-autonomous appliance*. A React SPA adds a whole Node/Vite/TS
  toolchain and a second dependency treadmill whose complexity a station console
  never repays.
- **Not a one-way door.** The UI is one module behind the **REST/WS API contract**
  (§5a); it can be swapped later (even to a SPA) without touching the engine. So
  the lean choice is low-risk.
- **Integration is API + data + coherence, not UI-merge.** doncel (central) will
  *talk to* many NG stations over the API in the fleet phase; the two UIs coexist,
  linked by the shared design system — they need not become one codebase.

Reverse this only if the station console grows into a large, app-like interface
with heavy client state — nothing in the four-pillar design (§8) suggests that.

---

## 5. System architecture

```
                          Browser (operator, remote)
                                   │  HTTPS + WSS
                                   ▼
                         ┌──────────────────┐
                         │   Caddy (TLS)    │   reverse proxy :443
                         └─────────┬────────┘
                                   ▼
            ┌──────────────────────────────────────────────┐
            │           e-Callisto NG Backend (FastAPI)      │
            │  REST API · WebSocket hub · Auth · Wizard      │
            │  Scheduler svc · Uploader svc · Job runner     │
            └───┬───────────────┬───────────────┬───────────┘
                │ SQLite (WAL)  │ filesystem    │ control bus (local)
                ▼               ▼               │ (Unix socket / shared mem)
        ┌────────────┐   /var/lib/callisto      ▼
        │  metadata  │   ├─ data/ (FITS)   ┌─────────────────────────┐
        │  users     │   ├─ quicklook/     │ Acquisition daemon(s)    │
        │  fileindex │   ├─ overview/      │  1 process per receiver  │
        │  schedules │   ├─ lightcurve/    │  · serial protocol       │
        │  jobs/audit│   └─ logs/          │  · state machine         │
        └────────────┘                     │  · FITS writer           │
                                           │  · live frame publisher  │
                                           └───────────┬─────────────┘
                                                       │ RS-232 / USB 115200
                                                       ▼
                                              Callisto receiver(s)
```

**Component responsibilities**

- **Acquisition daemon** (one per receiver): owns the serial port, runs the
  record/overview state machine, writes FITS + light curves + overviews,
  publishes live spectrum/waterfall frames and housekeeping to the control bus.
  Stateless w.r.t. UI; driven by config + commands.
- **Backend**: the only thing the browser talks to. Serves the API, the
  WebSocket hub (fans live frames out to clients), auth, the install wizard, the
  scheduler, and the uploader. Reads/writes SQLite and the filesystem; sends
  commands to daemons over a local **control bus** (Unix-domain socket or a small
  message queue) — start/stop/overview/reload-config.
- **Scheduler service**: computes sunrise/transit/sunset (astropy/skyfield) and
  materializes per-receiver schedules; issues start/stop/overview commands at the
  right UTC moments; recomputes daily.
- **Uploader service**: watches for completed FITS, gzips, ships to one or more
  central archives (FTP/SFTP), verifies, moves to dated backup, prunes by
  retention. Offline-tolerant queue with retry/backoff.
- **Job runner**: quicklook PNG generation, integrity checks, config
  backup/restore, log rotation.

The split means: **the web app can crash or be updated without interrupting
recording**, and a wedged receiver only affects its own daemon.

---

## 5a. Modularity, separation of concerns & extensibility

**Modularity and separation of duties are a primary design constraint, not an
afterthought.** The suite must absorb two kinds of change cheaply: *improving the
code* (replace/upgrade a part without ripple) and *growing the network* (add more
instruments, and add **new instrument types**). Everything below exists to make
those two cheap.

### Principles

- **Single responsibility per module.** Each component owns exactly one concern
  (acquire, schedule, upload, serve, render). No component reaches into another's
  internals.
- **Contracts, not implementations.** Components interact only through **explicit,
  versioned interfaces** — the control-bus message schema, the data-product
  schema, the REST/WS API, and the plugin interfaces below. Any implementation
  behind a contract is replaceable.
- **Dependency inversion at the edges.** Hardware, transports, output formats, and
  notifications are **plugins** the core depends on *abstractly*; concrete drivers
  are loaded from a registry. The core never imports a specific device or
  protocol.
- **Process isolation = fault isolation.** The runtime split (§5) is also a duty
  split: a crash/upgrade in one process can't corrupt another; each is
  independently deployable and restartable.
- **Stable seams, versioned everywhere.** Public API `/api/v1`, control-bus schema,
  data-product schema, and each plugin interface carry a version so producers and
  consumers evolve independently.

### Extension points (plugin interfaces)

Each is a small, documented interface with a registry; adding one is a
self-contained module that touches **no core code**:

| Plugin kind | Interface (capabilities) | First implementation(s) | Why it's a seam |
|---|---|---|---|
| **Instrument Driver** | `discover · connect · identify · configure · start/stop/overview · stream(spectra) · capabilities · close` (class-specifics like EEPROM channel upload stay *inside* the driver) | **Callisto receiver** (CD1316, fw 1.5/1.7/1.8) | new receivers, tuners, firmware, and SDRs are added as drivers |
| **Upload Transport** | `connect · put · verify · close` | FTP, SFTP | add HTTPS/S3/rsync without touching the queue |
| **Output Writer** | `filename · write(image, meta)` | Legacy FITS, Standard FITS, Custom | the §6a modes are just three writers; add more formats |
| **Schedule Rule** | `materialize(date, site) → events` | Sun-relative, Fixed-time | add moon/source-transit or external-trigger rules |
| **Quicklook/Export Renderer** | `render(file) → asset` | PNG spectrogram | add light-curve PNG, video, thumbnails |
| **Alert Channel** | `send(event)` | Email, Webhook | add Slack/Telegram/SMS |
| **Auth Provider** | `authenticate · identity` | Local user/password | add LDAP/OAuth/observatory SSO |

### The Instrument Driver abstraction (the key extensibility seam)

Growing the network has **two distinct meanings**, and the design separates them:

1. **More instruments of a known type** — add an instance: a config row + one
   `callisto-acq@<id>` daemon process. No code change; this is the everyday
   pairs/sets case. Scales by adding driver *instances* and station compute (§3).
2. **A new instrument *type*** — implement the **Instrument Driver** interface in
   a new module and register it. The acquisition daemon, scheduler, FITS writer,
   uploader, and UI all work against the **driver's declared `capabilities`**
   (bands, channels, calibration support, overview support, command set), so they
   need no changes. The current Callisto serial logic (§6) is simply *the first
   driver*, not the core.

A driver declares what it can do; the rest of the suite adapts to that
declaration (feature-detection, not hard-coding). This is what lets the **network
evolve with new instruments** without forking the platform.

### Instrument classes — the variation the driver seam must absorb

The platform must support **three classes of instrument on the same station**,
which differ fundamentally in **where the signal processing happens** (the
device↔host division of labor). This is the single most important reason the
driver boundary exists, and the boundary is deliberately placed *after* DSP:

| Class | Device does | Host (Pi/PC) does | Link | Host compute | Status |
|---|---|---|---|---|---|
| **1. Heterodyne (ADC + dumb MCU)** — *legacy e-Callisto* | analog tuning + single-channel ADC; MCU just relays | **everything**: drives the swept-tuning loop, programs channels into EEPROM, assembles the spectrum from the sweep, timing | serial 115200 | **low** but host owns the real-time acquisition logic | **known** — reuse existing Callisto code as the first driver |
| **2. SDR without FPGA** | streams raw **IQ samples** | **heavy host DSP**: FFT / channelize / detect / integrate raw IQ into spectra in software | USB3 / Ethernet (high BW) | **high** (CPU, possibly GPU/SIMD) — the compute-hungry case | make room |
| **3. SDR with FPGA** | on-board **FFT/channelization**, streams ready **power spectra** | light: ingest spectra, format, write, timestamp | USB3 / Ethernet | **low** | make room |

**Design implication — keep the driver boundary at "normalized spectra".** Every
driver, regardless of class, delivers the *same* internal product to the core: a
timestamped stream of **spectra/sweeps (time × frequency power)** + housekeeping +
a `capabilities` descriptor. Where those spectra came from — a host-driven serial
sweep (class 1), host software DSP on IQ (class 2), or an FPGA (class 3) — is
**entirely inside the driver**. So:

- The **core, FITS writer, scheduler, uploader, live pipeline, and UI never know
  the instrument class** — they consume normalized spectra and the capabilities
  descriptor. Nothing heterodyne-specific (serial, swept single-ADC, EEPROM
  channel table, 8-bit) leaks into the core; those are class-1 driver internals.
- An SDR driver internally hosts an **optional, pluggable host-side DSP pipeline**
  (class 2) or a thin ingest stage (class 3). DSP is a driver concern, not a core
  concern.
- `capabilities` must be rich enough to span all three: bandwidth, channel
  count/spacing (native vs. synthesized), sample/sweep rate, **bit depth /
  dynamic range** (SDR ≫ 8-bit), tuning model, calibration support,
  **`processing_location` = host | device | hybrid**, and **`link`** (see below).

**Device connection is a driver concern, and the medium varies by class.** Each
driver owns *how it reaches its instrument* via a shared **Connection** helper
abstraction with interchangeable backends — **serial-over-USB** (class-1
e-Callisto, per legacy code), **USB bulk** (class-2 dongles, e.g. SoapySDR), and
**TCP/Ethernet** (class-3 FPGA appliances, also USB). Consequences the platform
bakes in now:
- **Discovery is per-medium and per-driver** — `/dev/serial` scanning (§6) is
  *class-1-specific*; USB enumeration and **network discovery (host:port / mDNS)**
  are first-class too. A driver advertises how to find and address its devices.
- An instrument instance is addressed by a **stable handle** that may be a `/dev`
  symlink, a USB id, *or* an `IP:port` — the core stores an opaque address, never
  assumes a local device file. (Don't confuse this device-side **Connection** with
  the outbound **Upload Transport** plugin — different seam, different direction.)

**Two knock-on effects already accounted for elsewhere:**
- **Compute sizing (§3) is class-driven, not just instrument-count-driven.** A
  class-2 SDR doing wideband host DSP can demand an x86/GPU station, while a Pi
  comfortably runs class-1 and class-3. The one-process-per-instrument model lets
  a single station mix a light heterodyne and a heavy SDR — size the box to the
  heaviest driver it hosts.
- **Output Writers (§6a) must not assume 8-bit.** The *Legacy* writer downconverts
  to 8-bit for archive compatibility; *Standard*/*Custom* writers preserve the
  SDR's higher bit depth / float. The driver reports bit depth; the writer decides.

### Code organization

- **Monorepo, clearly bounded packages**: `core` (domain models + contracts),
  `drivers/*` (instrument drivers), `transports/*`, `writers/*`, `services/*`
  (acquisition, scheduler, uploader, jobs), `api` (FastAPI backend + Jinja portal +
  static islands; consumes the shared M3 design system). Imports flow **inward
  toward `core`**; `core` depends on nothing concrete.
- **Each package independently testable** against its contract, with fakes (serial
  simulator, fake transport, fixed-clock ephemeris) so modules are verified in
  isolation in CI — a prerequisite for safely *improving the code*.
- **Plugins are discoverable** via entry points, so third parties (an observatory
  with a custom receiver or archive) ship a driver/transport as a separate package
  without patching the suite.

---

## 5b. Licensing & plugin governance

Because modularity and a third-party plugin ecosystem are first-class goals
(§5a), licensing and interface governance are design concerns, not legal
afterthoughts.

- **Core license (recommended, pending sign-off):** the **core + reference drivers
  + web app under a strong copyleft license** — GPLv3 for continuity with the
  legacy Linux daemon (GPLv3), or **AGPLv3** since this is a network-served
  application (closes the "SaaS loophole" so improvements flow back). Final choice
  is the owner's call; the rest of this section assumes copyleft core.
- **Plugins can be independently licensed — by design.** Drivers/transports/etc.
  are loaded over **stable, documented IPC/contract boundaries** (the control bus
  and plugin interfaces), and the acquisition driver already runs as a **separate
  process** (§5). Communicating across a defined IPC rather than linking into the
  core means a **vendor can ship a closed-source instrument driver** (e.g. for a
  proprietary FPGA SDR) without it being a derivative work of a copyleft core.
  This is a deliberate architecture↔licensing synergy: process isolation buys
  both fault isolation *and* licensing flexibility.
- **Interface stability promise (governance).** Every plugin contract is
  **semver-versioned** with a published **deprecation policy** (e.g. an interface
  major version is supported for N releases after a successor ships). The core
  advertises which contract versions it supports; plugins declare which they
  target. This is what makes "third parties build on us" safe.
- **Plugin registry & provenance.** An optional registry lists known
  drivers/transports with their supported contract versions and maintainers;
  installed plugins are visible in the UI with their version, license, and
  signature status.
- **Contribution & trademark.** A contribution model (DCO/CLA — owner's call) and
  protection of the **"e-Callisto" name/marks** so forks/derivatives don't imply
  official endorsement.

> **Open decision:** GPLv3 vs. AGPLv3 for the core, and whether a CLA is required.
> Either way, the **process-isolated plugin boundary keeps third-party (incl.
> closed) drivers viable**, which matters for SDR/FPGA vendors.

---

## 6. Hardware abstraction & acquisition

> This section describes the **Callisto Instrument Driver** — the *first*
> implementation of the Instrument Driver interface (§5a), and the **class-1
> heterodyne** case (ADC + dumb MCU, fully host-driven). It is one plugin, not the
> core: the planned **class-2 SDR (host DSP)** and **class-3 SDR+FPGA** drivers
> ship as sibling modules implementing the same interface and emitting the same
> normalized spectra, and the rest of the suite adapts to each driver's declared
> `capabilities`. The serial/sweep/EEPROM logic below is **class-1-specific** and
> stays inside this driver.

- **Device discovery:** scan `/dev/serial/by-id/*` and `/dev/ttyUSB*`; for each,
  open at 115200 8N1, send the identify/`?` sequence, parse the response to
  confirm it's a Callisto and **detect firmware (1.5/1.7/1.8)** → derive
  `if_init`, 10-bit flag, EEPROM-info behavior (as the legacy Linux daemon does).
- **Protocol layer:** a typed wrapper over the receiver's ASCII command set
  (`F0`, `O`, `L`, `S1/S0`, `GE/GD`, `FS`, `FE…` channel upload, `T/GS/GA`,
  overview `T0 M2 %5 F0045.0 L13200 P2`). This is the *one* place that knows the
  wire protocol; everything else calls semantic methods (`tune`, `set_gain`,
  `upload_channels`, `start`, `stop`, `overview`).
- **Channel/EEPROM:** compute PLL divider bytes (0.0625 MHz step) + band select,
  upload, and **read back & verify** (keep the Linux daemon's verification step).
- **Acquisition state machine:** STOPPED→STARTING→RUNNING→OVERVIEW with
  double-buffering; parse the hex data stream, 10-bit→8-bit; detect data-loss /
  hardware-reset / timeout and self-recover.
- **Outputs (per file period, default 15 min):**
  - **FITS**: 8-bit time×frequency image, full standard header (DATE/TIME-OBS,
    OBS_LAT/LON/ALT, FRQFILE, PWM_VAL, axes).
  - **Light curves**: per-channel time series for flagged channels.
  - **Spectral overviews**: `.prn` (and modern `.parquet`/`.csv`) on demand or by
    schedule.
  - **Live frames**: streamed to the backend for the browser waterfall (not
    persisted, or ring-buffered briefly).
- **Output compatibility mode (per instrument):** the file naming + FITS
  header/format conventions are selectable (see §6a):
  - **Legacy** — byte-compatible filenames/headers/`scheduler.cfg` for drop-in
    flow into the existing e-Callisto archive.
  - **Standard** — modern, well-formed FITS the archive still accepts, without
    legacy quirks.
  - **Custom** — operator-defined naming template and optional extra header keys.
- **Units & scaling — raw ADC is the default (§6b).** Stored data and displays are
  **raw ADC / digits** unless the instrument is **explicitly calibrated**. The
  suite does **not** estimate dB or apply log scaling by default; dB is an
  **optional** view/processing choice, and physical units (SFU/Kelvin) require an
  explicit calibration. (A deliberate departure from the legacy tools, which
  auto-convert to dB.)
- **Calibration (ships in v1, optional):** SFU and antenna-temperature (Kelvin)
  modes via calibration coefficient files — modeled on the Windows `CALxxxxx`
  flow but managed through the UI. Off by default; enabling it is a per-instrument
  choice with an uploaded/edited coefficient set.

### 6b. Units & scaling policy

Three explicit levels, **defaulting to the rawest**; the suite never silently
transforms values:

| Level | What it is | Default? | Requires |
|---|---|---|---|
| **Raw ADC / digits** | the instrument's native sample values, stored as-is | **yes — always the default** | nothing |
| **dB (log-scaled estimate)** | `10·log10`/`mV→dB`-style scaling of raw values — a *display/processing estimate*, **not** a physical calibration | **no — opt-in** | a per-instrument toggle (and a stated reference) |
| **Calibrated (SFU / Kelvin)** | physically meaningful flux/temperature | **no — opt-in** | an explicit calibration + coefficient set |

Rules:
- **Persisted science data is raw ADC** unless the instrument is explicitly
  calibrated; then the calibrated product is written with the correct `BUNIT`
  (`digits` by default). dB is **never** the stored unit — it is a derived view.
- **dB ≠ calibration.** dB is a convenience log scaling for *looking* at data; it
  asserts nothing physical. It is offered as an **optional toggle** in viewers and
  as an optional per-instrument processing choice, off by default.
- **Live viewers default to linear/raw**; dB and calibrated views are explicit
  user toggles (see §8.1).
- Every product records *which* level produced it, so raw, dB-estimated, and
  calibrated data are never confused downstream.

### 6a. Output compatibility modes

A single switch per instrument selects how data products are named and
structured, so one suite serves both the existing archive and modern pipelines:

| Mode | Filenames | FITS header | Schedule export | Use |
|---|---|---|---|---|
| **Legacy** | exact `INSTRUMENT_YYYYMMDD_HHMMSS_FC.fit`, `OVS_*.prn`, `LC*` | legacy key set/order | `scheduler.cfg` | drop-in to current e-Callisto archive |
| **Standard** | same pattern, cleaned | complete, conventional FITS/WCS | modern + optional legacy | new deployments wanting clean data |
| **Custom** | operator template (tokens: instrument/date/fc/band…) | base + custom keys | per-target | bespoke institutional pipelines |

Upload targets can each declare which mode they expect, so a station can ship
**legacy to the central archive and standard/custom to a local mirror**
simultaneously.

---

## 7. Data model & storage

**Filesystem** (`/var/lib/callisto/`):
```
data/<instrument>/<YYYY>/<MM>/<DD>/<INSTRUMENT>_YYYYMMDD_HHMMSS_FC.fit
quicklook/<...>.png            # auto-generated spectrogram thumbnails
overview/<instrument>/OVS_*.prn
lightcurve/<instrument>/LC_YYYYMMDD_*.{csv,parquet}
backup/<...>                   # post-upload dated archive (optional)
logs/
config/                        # exported config snapshots
```

**SQLite tables (sketch):**
- `station` — this station's identity: station name/id, **observatory** name/id it
  belongs to, contact, default coordinates. (Single row in v1; carries the
  observatory reference so files and config are fleet-attributable later.)
- `instruments` — id, **station-scoped**, name, serial-device, firmware,
  lat/long/alt, origin, focuscode, gain, calibration profile, output mode,
  enabled.
- `frequency_programs` — id, name, channel list (freq, lc-flag), sweep length,
  sweeps/sec, LO, source (manual/generated-from-overview).
- `schedules` — id, instrument, rule (sun-relative or fixed), entries, margins.
- `files` — path, instrument, start/end UT, rows×cols, size, checksum, upload
  state, quicklook path. (Index over the FITS on disk.)
- `upload_targets` — host, protocol (FTP/SFTP), creds (encrypted), path template,
  output mode, **dispatch_mode** (immediate / scheduled / manual) + **window**
  (for scheduled), bandwidth/concurrency caps, enabled; `upload_jobs` — file,
  target, state, attempts, next-attempt, last error.
- `users`, `sessions`, `roles`, `audit_log`.
- `settings` — global (site, TLS, NTP policy, retention), `wizard_state`.
- `events`/`alerts` — health and notifications.

Secrets (FTP passwords, etc.) encrypted at rest with a key derived from a
machine-bound secret; never returned in plaintext via the API.

---

## 8. Web application structure

The UI is organized into **four top-level pillars**. Everything the operator
does lives under one of them; each pillar maps to a cluster of API resources and
(where relevant) daemon capabilities. The install wizard (§9) is simply the
**guided first-run mode of the Instrument Configurator**, not a separate area.

```
e-Callisto NG  (one Station)
├─ Operations           — operate & monitor this station's instruments (cockpit)
├─ Instrument Configurator — set up each instrument (wizard = its guided mode)
├─ Tools                — run diagnostics, generation, calibration
└─ Station Settings     — the station, access, users, software
```

> The **observatory-level "Fleet" view** (overseeing *multiple stations*) is a later
> phase that sits **above** these four — it aggregates many stations' Operations
> into one cross-station cockpit. Within a single station, v1 is the four pillars
> below.

### 8.1 Operations — *operate & monitor this station*

The operational cockpit over the **instruments of this station**. Read-heavy,
real-time, for day-to-day running. (At the org level this is what the future
Fleet view aggregates across stations.)

- **Overview dashboard** — per-instrument recording state, live mini-waterfall,
  current frequency program, next scheduled action, disk free, NTP/clock status,
  last upload, active alerts; quick **start/stop/overview** per instrument.
- **Live Viewer** — full-screen real-time **waterfall spectrogram** (WebGL) plus
  single-spectrum and light-curve live panels; color map, zoom, freeze/snapshot,
  channel cursor readout. **Defaults to raw ADC / linear**; dB and (if calibrated)
  SFU/Kelvin are explicit opt-in toggles, never automatic (§6b). Switchable per
  instrument.
- **Data Browser** — searchable catalog of FITS files (date/time/instrument/focus
  code), calendar/heatmap, quicklook thumbnails, in-browser FITS viewer,
  single/bulk **download**, delete, re-queue. Light-curve & overview browsers.
- **Distribution (operational)** — upload **queue / history / failures**, manual
  "send now", per-file status across targets. (Target *configuration* — where to
  send, credentials, dispatch mode — lives in **Station Settings → Distribution**,
  §8.4.)
- **Health & alerts** — live status feed; data-loss/disk/clock/upload warnings.

### 8.2 Instrument Configurator — *set up each instrument*

Per-instrument definition. The **wizard** walks these in order on first run; the
same screens are the permanent editors afterward. Instrument-scoped throughout.

- **Identity** — name, observatory/origin, **coordinates** (lat/long/alt, map
  picker, cloneable), focus code, gain/PWM, clock source, file length,
  **output compatibility mode** (legacy/standard/custom, §6a).
- **Frequency Programs** — create/edit/import; **auto-generate from a spectral
  overview** (quietest/least-RFI channel per step, RFI-exclusion band on the
  plot — the GenFrqPrg capability, web-native); preview over the overview;
  activate.
- **Schedule** — **sun-relative** (sunrise→sunset + margins + midday restart +
  optional sunset overview, from coordinates) and/or fixed-time rules; 24-h
  timeline preview; staggered per instrument. (Replaces SchedulerGeni +
  callisto-sunschedule.)
- **Calibration setup** — stored unit defaults to **raw digits**; optionally
  enable physical units (SFU/Kelvin) by attaching a coefficient set, and/or allow
  an optional dB view. Off by default — raw unless explicitly calibrated (§6b).
- **Add / clone / import** — add an instrument, clone from an existing one, or
  import config from another station (provision a second station identically).

### 8.3 Tools — *run things*

Utilities the operator actively runs, mostly for commissioning, troubleshooting,
and calibration. Modeled on the legacy bench/utility apps, web-native.

- **Diagnostics / Bench** — live detector-voltage readout, manual frequency sweep
  with amplitude plot, **noise-figure (Y-factor)** & bandpass workflows,
  focus/relay switching, AGC linearity (NoiseFigurePlotter + `simple`).
- **Manual overview** — trigger a spectral overview sweep on demand and view it.
- **Calibration runs** — execute/track calibration recordings, manage coefficient
  sets, show which files were produced calibrated.
- **Frequency-program generator** — the overview→program workflow as a standalone
  tool (also reachable from the Configurator).
- **Import (migration)** — import a legacy station's config/programs/schedule/
  calibration and index existing FITS in place (§9a); also the config import/clone
  path for provisioning.

### 8.4 Station Settings — *the station & the suite*

Everything about the station (host) and the application rather than the science.

- **Access** — remote-login mode (LAN/VPN · public-HTTPS+DDNS · reverse tunnel),
  hostname/TLS, dynamic-DNS, reachability test (§10).
- **Distribution (destinations)** — define **where files go**: add/edit upload
  **targets** (host, FTP/SFTP, credentials, path template, output mode), set each
  target's **dispatch mode** (immediate on-ready · overnight/scheduled window ·
  manual), bandwidth/concurrency caps, and test the connection. (The live queue
  itself is in Operations → Distribution, §8.1.)
- **Users & Access** — accounts, roles, sessions, password/security policy,
  **audit log**.
- **Time** — NTP/chrony status & drift, enforcement policy.
- **Storage** — usage, retention rules, backup location.
- **Software** — version, **updates** (channels, rollback), config
  **backup/restore**.
- **System** — network info, services health, journald **log viewer**, receiver
  reconnection, reboot/shutdown.

---

## 9. Install wizard (first-run)

A guided, resumable, web-based flow that runs the **very first time** the suite
is opened (and re-runnable later). Until completed, the app redirects all routes
to the wizard. State persisted in `settings.wizard_state` so a refresh/reboot
resumes mid-flow.

**Steps:**

1. **Welcome & license.** Intro, version, GPL/licensing acknowledgment.
2. **Create administrator.** First user: username + strong password (this is the
   *only* unauthenticated step; creating it immediately enables login). Optional
   recovery email.
3. **Instruments on this station.** The suite is always multi-instrument; this step
   just lets you **add one receiver (default) or several** — no single-vs-multi
   mode to choose. Detected receivers are listed; add each you want to use. The
   subsequent hardware/identity/program/schedule steps run **once per added
   instrument**, with **clone-from-first** (e.g. same coordinates, different
   band/focus) and **import-config-from-another-station** to provision a second
   station identically. Adding just one instrument is the streamlined
   single-instrument path with no extra friction.
4. **Access & remote-login mode.** Hostname/access URL, session policy, and the
   **remote-access mode** (LAN/VPN-only · public-HTTPS+DynamicDNS · reverse
   tunnel/relay — see §10). Dynamic-IP friendly: if the operator picks public or
   relay, the wizard sets up DDNS/tunnel and verifies reachability before
   continuing. Defaults to LAN-only.
5. **Time sync.** Verify NTP/chrony is active and synced; offer to configure it;
   **block progress if the clock is unsynced** (with override + warning), because
   data timing depends on it.
6. **Detect hardware** *(per added instrument).* Scan serial ports,
   identify connected receiver(s) and firmware; name and confirm each (stable
   `by-id` binding so pairs don't swap on reboot). "Not found → re-scan / check
   cabling" help, mirroring the legacy COM-check step.
7. **Station identity** *(per instrument).* Instrument name (alphanumeric +
   dash), observatory/origin label, **coordinates** (lat/long/altitude — map
   picker, cloneable across instruments), focus code, default gain, and the
   **output compatibility mode** (legacy / standard / custom, see §6a).
8. **Frequency program** *(per instrument).* Choose a bundled default, import one,
   or **run a live spectral overview now and auto-generate** a program from it.
9. **Calibration (optional).** Skip (raw digits) or enable SFU/Kelvin by
   uploading/selecting a calibration coefficient set per instrument.
10. **Schedule** *(per instrument).* Enable sun-relative recording from the
    entered coordinates (sunrise→sunset + margins, midday restart, optional
    overview), or set fixed times; preview the day. Multi-instrument schedules
    can be staggered.
11. **Data & distribution.** Storage location & retention; optionally configure
    one or more central-archive upload targets (host, protocol, credentials, path
    template, **per-target output mode**, and **dispatch mode** — immediate
    on-ready / overnight window / manual) — skippable and editable later.
12. **Review & launch.** Summary of all instruments and choices; on confirm, the
    suite writes config, enables systemd services, starts the acquisition
    daemon(s), and lands on the live Dashboard.

Design rules: every step has sane defaults, inline validation, and a "skip for
now" where safe; nothing requires a terminal; the wizard is itself just the API +
UI, so the same screens serve as the permanent per-section editors.

### 9a. Migration from legacy stations

Every early adopter is an **existing Callisto station**, so onboarding must be an
**import, not a re-setup**. Offered as a branch in the wizard ("I'm migrating an
existing station") and as a permanent **Tools → Import** action.

- **Inputs:** point at an existing install folder or upload the legacy config
  files. The importer parses:
  | Legacy artifact | Imported into |
  |---|---|
  | `callisto.cfg` | instrument identity — COM/serial port, instrument name, origin, **lat/long/altitude**, focus code, gain/PWM, clock source, file length, paths |
  | `frqXXXXX.cfg` | frequency programs (channel list, sweep length, sweeps/sec, LO, light-curve flags) |
  | `scheduler.cfg` | schedule, **converted to NG rules** (sun-relative where it matches, else fixed-time) |
  | `CALxxxxx.prn` | calibration coefficient set(s) |
  | existing `*.fit` on disk | **indexed in place** (registered in the catalog + quicklooks generated), *not* re-uploaded |
- **Defaults for continuity:** a migrated instrument is set to **Legacy output
  mode** (§6a) and **raw ADC** units (§6b) so its data keeps flowing into the
  archive byte-identically.
- **Safety:** the import is **preview-then-commit**, **non-destructive** (never
  touches the legacy install or its data), idempotent, and re-runnable. Unmapped
  or ambiguous fields are surfaced for the operator to confirm.
- **Outcome:** an existing station moves to NG in minutes with its identity,
  programs, schedule, calibration, and historical data intact.

---

## 10. Authentication, authorization & security

- **Remote login (user + password).** Argon2id-hashed passwords; login issues a
  secure, HTTP-only, SameSite session cookie (server-side session in SQLite);
  short idle + absolute timeouts; CSRF protection on state-changing requests.
  (JWT optional for API/automation tokens.)
- **Roles (RBAC):**
  - **Admin** — full control incl. users, system, updates, upload credentials.
  - **Operator** — start/stop/overview, edit frequency programs/schedules,
    manage data, but not users/system secrets.
  - **Viewer** — read-only dashboards, live view, data browsing/download.
  - **API token** — scoped, for scripting/integration.
- **Transport:** HTTPS everywhere via Caddy (self-signed by default, real certs
  if a domain is provided); WSS for live streams; HSTS when using real certs.
- **Remote-access modes (all three shipped, operator picks in the wizard).**
  Because most stations are on **dynamic IP behind NAT**, the suite cannot assume
  a reachable public address:
  1. **LAN / VPN only (default, closed).** Bind to the local network; reach it
     over the campus LAN or an existing VPN. Safest; recommended default.
  2. **Public HTTPS with Dynamic DNS.** For sites that can port-forward: built-in
     **dynamic-DNS** updater (so a changing IP stays reachable by hostname) plus
     automatic Let's Encrypt certs, hardened by 2FA + lockout + HSTS.
  3. **Outbound reverse tunnel / relay.** For NATed/dynamic-IP sites that can't
     forward ports: the station opens an **outbound connection to a relay** and is
     reached through it — no inbound firewall changes, no static IP needed. Ideal
     for the typical observatory-behind-NAT deployment.
  The mode is changeable later in **System → Access**; switching modes never
  exposes the station without explicit confirmation.
- **Secrets:** upload/FTP credentials encrypted at rest, never echoed back;
  write-only fields in the UI.
- **Hardening:** rate-limited login + lockout/backoff, audit log of
  auth + privileged actions, optional bind to LAN/VPN only, optional 2FA (TOTP)
  for admins, brute-force-resistant defaults. First-boot forces creating the
  admin (no default credentials — a deliberate break from "ask the PI for the
  password" era).
- **Threat posture:** the station may be exposed on a home/campus network; assume
  hostile internet. Default to closed (LAN-only) and let the operator opt into
  exposure.

---

## 11. Real-time data pipeline

1. Daemon assembles each sweep → emits a compact **binary frame** (timestamp +
   N channel bytes) on the control bus.
2. Backend **WebSocket hub** receives frames, maintains a short ring buffer, and
   fans out to subscribed browser clients (downsampling/throttling per client if
   needed).
3. Browser renders incrementally: append a column to the WebGL waterfall, update
   the live spectrum and selected light-curve channels.
4. Housekeeping (buffer load, voltages, state, disk) streamed on a separate, slow
   channel to drive the dashboard.

Backpressure-aware: slow clients get decimated frames, never block acquisition.
Live frames are ephemeral; the **authoritative record is the FITS on disk**.

---

## 12. Scheduling

- Compute sunrise / **transit** / sunset for the site with **astropy/skyfield**
  (accurate, dependency-light, no Emacs) including horizon elevation margin and
  polar day/night.
- Materialize a per-instrument daily schedule: start at sunrise+margin, **restart
  at transit** (fresh file / resilience), stop at sunset−margin, optional
  overview after sunset. Plus arbitrary fixed-time rules.
- Scheduler service issues start/stop/overview commands at the right UTC instant
  and recomputes at local midnight; the UI shows the live timeline and "next
  action".
- Schedules are data (DB), versioned and editable; no generated `.cfg` files to
  hand-tend (though export to legacy `scheduler.cfg` format is available for
  interop).

### 12a. Timing & clock discipline

**Accurate, continuously-disciplined UTC is foundational** — every scientific
value the network produces is only as good as its timestamp.

- **Continuous synchronization is paramount.** chrony/NTP runs **always and
  resyncs regularly**, not once at boot. The station continuously tracks **offset
  and drift**; this is monitored as a first-class health metric (§14) and is a
  gating condition for recording.
- **Drift policy (ties to §14a):** within threshold → record normally; beyond a
  *warn* threshold → keep recording but **flag the data quality** and alert;
  beyond a *hard* threshold → **pause recording** (configurable) until resync.
- **Per-class timestamping model** — the driver stamps acquisition time, and the
  precise per-sample axis (FITS `CRVAL1`/`CDELT1`) is back-computed from the
  device's known rate rather than per-frame wall-clock jitter:
  | Class | Time source | Notes |
  |---|---|---|
  | 1 Heterodyne | host clock at buffer fill + known serial latency | as legacy, but latency-compensated |
  | 2 SDR (host DSP) | host clock at sample-block boundary; rate from SDR sample clock | account for USB/buffer latency |
  | 3 SDR + FPGA | device/stream timestamp where provided, else host clock | FPGA may expose precise timing |
- **Holdover:** if the NTP source is lost (offline station), keep running on the
  last-good discipline and **flag growing timing uncertainty**; recording isn't
  silently trusted as accurate.
- **High-accuracy option (future):** GPS/PPS disciplining as an optional add-on
  for stations needing sub-ms absolute timing (e.g. burst timing studies).
- **Provenance:** each FITS records the timing source and a quality indicator so
  downstream users know how much to trust the timestamps.

---

## 13. Data management & upload

- **Indexing:** every written FITS is registered (start/end UT, geometry,
  checksum, quicklook).
- **Quicklook:** background job renders a PNG spectrogram per file for fast
  browsing.
- **Destinations are defined in Station Settings.** *Where* files go — the one or
  more upload **targets** (host, protocol FTP/SFTP, credentials, path template,
  output mode per §6a, and **dispatch mode** below) — is configured under
  **Station Settings → Distribution** (see §8.4). The **Operations → Distribution**
  view (§8.1) is the operational side: queue, history, failures, retry, "send
  now". Config vs. operation are deliberately separated.
- **Dispatch mode (per target).** When files are sent is selectable:
  1. **Immediate (on-ready, default)** — each FITS is dispatched **as soon as it
     is written and closed**, the moment it's ready. Lowest latency to the
     archive; best on stable links.
  2. **Overnight / scheduled window** — files are **queued during the day and
     sent in a configured window** (e.g. 02:00–05:00 local, or "after sunset").
     Good for metered/slow/shared links and to keep daytime bandwidth free.
  3. **Manual only** — held until an operator clicks "send now".
  A target can also cap concurrency/bandwidth; modes are per-target, so a station
  can push **immediately to the central archive but batch a bulky mirror
  overnight**.
- **Upload mechanics:** gzip → transfer using a `.tmp`-then-rename handshake
  (avoids partial-read races, as the legacy scripts do) → verify → move to dated
  backup → mark uploaded. **Multi-target** (e.g. FHNW + a mirror), **offline
  queue** with retry/backoff that holds files until the link returns regardless of
  dispatch mode.
- **Retention:** configurable by age/free-space; prune local data after confirmed
  upload + backup; never delete un-uploaded data without explicit consent.
- **Integrity:** checksums; optional periodic re-verification.

---

## 14. Observability, health & alerting

- **Health checks:** recording liveness, serial connectivity, **clock sync /
  drift**, disk free, upload backlog, temperature/throttling (Pi-specific), data
  gaps. Distinguish **system health** from **data quality** (saturation/clipping,
  dead/flat channels, dropouts, RFI level) — the latter raises data-quality flags
  on affected files, not just system alerts.
- **Failure-mode handling:** see §14a for the consolidated degrade-don't-die
  policy that these checks feed.
- **Alerts:** surface in the dashboard and optionally push via **email/webhook**
  (e.g. on data loss, disk near-full, clock drift, upload failures, receiver
  disconnect).
- **Logs:** structured logs to journald; in-app log viewer with filtering;
  rotating file logs for the science record.
- **Metrics (optional):** Prometheus endpoint for sites that want external
  monitoring.

### 14a. Failure modes & degraded operation

A single explicit policy, so behavior is consistent rather than ad-hoc. **Guiding
principles: degrade, don't die; never silently lose science data; isolate faults;
always alert.**

| Condition | Detection | Automatic response | Operator signal |
|---|---|---|---|
| **Disk near-full / full** | free-space watch vs. thresholds | warn early; at hard limit **stop recording — never overwrite un-uploaded data** (optional ring-buffer for non-critical only) | alert + dashboard |
| **Clock unsynced / drift** | continuous NTP monitor (§12a) | warn → flag data quality → hard threshold **pauses recording** (configurable) | alert |
| **Instrument/device lost** (serial/USB/Ethernet drop) | I/O timeout | reconnect with backoff; reset/re-init driver; **other instruments unaffected** (process isolation) | alert if persistent |
| **Hardware reset detected** | device reset message | re-init and resume automatically | log + alert |
| **Upload target down** | transfer failure | **offline queue** with retry/backoff; files held, never lost (any dispatch mode) | alert if backlog grows |
| **Power loss mid-file** | restart after outage | atomic `tmp`-then-rename writes mean no corrupt FITS; flush partial buffer on clean shutdown; resume schedule on boot | startup log |
| **SDR DSP overrun** (class-2) | host can't keep up | **degrade gracefully** — drop frames / reduce resolution / log, rather than crash | alert + sizing hint (§3) |
| **Web/app crash** | systemd | restart; **acquisition daemons unaffected** (separate processes) | log |
| **Invalid config / bad edit** | validation on apply | reject and keep last-good; safe rollback | inline error |

Cross-cutting: faults are **contained to one process/instrument**; recording is
**independent of the web app**; and any degraded state is **always surfaced** as
an alert plus a data-quality flag on affected files.

---

## 15. Packaging, deployment & updates

- **Primary:** a **`.deb`** for **Debian and Raspbian**, built for both **arm64
  and amd64**, that installs the app (Python venv or bundled), systemd units
  (`callisto-web`, `callisto-acq@<instrument>` — one templated unit instance *per
  instrument*, so multi-instrument stations just enable more), `callisto-scheduler`,
  `callisto-uploader`, Caddy config, and creates `/var/lib/callisto` +
  `/etc/callisto`. `apt install ecallisto-ng` on any Debian/Raspbian box → open
  browser → wizard. Same package on a Pi or an x86 server.
- **Convenience:** a **prebuilt Raspberry Pi OS image** (and optionally a generic
  Debian image / cloud-init) with the suite preinstalled for non-technical users —
  flash/boot, browse to the wizard.
- **Updates:** in-app "check for updates" (admin) → apt/OTA update with health
  rollback; release channels (stable/beta).
- **Config as data:** all settings live in SQLite/`/etc/callisto`; **backup &
  restore** from the UI; reproducible re-provisioning.
- **Dev:** Docker Compose with a **serial simulator** (fake Callisto emitting
  realistic frames) so the whole stack runs without hardware.

---

## 16. API surface (sketch)

REST (OpenAPI-documented), all under `/api/v1`, plus WebSockets:

```
POST   /auth/login            POST /auth/logout         GET /auth/me
GET    /instruments           POST /instruments         PATCH /instruments/{id}
POST   /instruments/{id}/start  /stop  /overview        (operator)
GET    /instruments/{id}/status
GET    /freq-programs         POST /freq-programs       POST /freq-programs/generate (from overview)
GET    /schedules            POST /schedules            GET /schedules/{id}/preview
GET    /files?from&to&instrument   GET /files/{id}      GET /files/{id}/download  /quicklook
GET    /overviews   /lightcurves
GET/POST /upload/targets      GET /upload/queue         POST /upload/{file}/retry
GET    /system/health  /storage  /clock  /version       POST /system/update  /backup  /restore
GET/POST /users               GET /audit
GET    /wizard/state          POST /wizard/step/{n}
WS     /ws/live/{instrument}      # waterfall+spectrum frames
WS     /ws/housekeeping/{instrument}
WS     /ws/events                # alerts/health stream
```

---

## 17. Non-functional requirements

- **Reliability:** acquisition independent of web app; auto-restart; survives
  reboot/power loss; resumes schedule; no data loss on clean shutdown (flush
  buffer).
- **Performance:** live waterfall ≥ real-time on a Pi 4 with ≥1 receiver; UI
  responsive over a slow WAN (lazy data, thumbnails, pagination).
- **Footprint:** runs in <512 MB app RAM; **single Python toolchain, no Node/SPA
  build**; no heavyweight broker/DB.
- **Portability:** ARM64 + x86-64 Debian.
- **UI coherence:** consumes the shared framework-agnostic **M3 design system**
  (Nebula/Supernova) so the station portal is visually coherent with doncel.dev
  without sharing its rendering stack (§4a).
- **Interoperability:** FITS, light curves, overviews, and optional
  `scheduler.cfg` export remain compatible with the existing e-Callisto ecosystem.
- **Accessibility/i18n:** keyboard-navigable, responsive (works on a phone for
  quick checks), translatable strings (the network is global).
- **Maintainability:** typed end-to-end (Pydantic ↔ TS from OpenAPI); tests
  incl. a serial simulator for CI.
- **Modularity:** every component sits behind a versioned contract (§5a); the
  Instrument Driver, transport, writer, schedule-rule, renderer, alert, and auth
  interfaces each have ≥1 implementation plus a fake, and a new implementation
  ships as a standalone package without core changes.

---

## 18. Roadmap / phases

- **M0 — Core contracts + record loop:** define `core` domain models and the
  **Instrument Driver / writer / transport interfaces** first; implement the
  Callisto driver + FITS writer + acquisition daemon against them, with a serial
  simulator; CLI only. (Getting the seams right here is what makes M1–M5 cheap.)
- **M1 — Backend + portal + auth + wizard:** FastAPI, SQLite, login/RBAC, the
  **Jinja portal shell wired to the shared M3 design system** (Nebula/Supernova),
  install wizard, instrument setup, start/stop.
- **M2 — Live & data:** WebSocket **waterfall JS island**, live viewer, data
  browser + quicklooks + download.
- **M3 — Programs & scheduling:** frequency-program editor + overview-based
  generation, sun-relative scheduler.
- **M4 — Distribution & health:** uploader (multi-target, offline queue),
  health/alerts, system section, updates.
- **M5 — Calibration & diagnostics:** calibration workflow, bench/noise-figure
  tools, multi-instrument polish, packaging (.deb + SD image).
- **M6+ (post-v1) — SDR classes:** **class-2 SDR (host DSP)** and **class-3
  SDR+FPGA** drivers, plus USB-bulk and network connection backends. v1 ships
  **class-1 heterodyne** only, but the §5a driver seam, the normalized-spectra
  boundary, the non-8-bit writers, and the class-agnostic connection layer are
  built in M0 so these drop in **without core changes**. "Make room now, build the
  SDR drivers later."

---

## 19. Key decisions made & open questions

**Technology decisions (defaulting rather than blocking):**
- All-Python backend+daemon (one stack, low barrier) with acquisition isolated as
  its own supervised process; compiled daemon reserved as a fallback.
- **Frontend: server-rendered Jinja portal + JS islands + shared M3 design system
  — not a SPA** (§4a). Single Python toolchain for a low-power appliance; visual
  coherence with doncel.dev via the framework-agnostic design system; UI swappable
  behind the API contract.
- Caddy for TLS; systemd supervision; native `.deb` (Debian/Raspbian, arm64+amd64)
  over Docker.
- No default credentials; admin created in the wizard.

**Product decisions (resolved with the owner):**
- **Audience:** universities deploying **pairs/sets** are the primary case →
  **multi-instrument is the always-on model**; a single station is just N=1, with
  **no single-vs-multi mode** to select and no extra wizard friction. Keep
  config import/export so a second station provisions from the first; full
  multi-*station* (fleet)
  fleet orchestration is a later phase but the data model stays fleet-ready.
- **Remote access:** ship **all three** modes — LAN/VPN-only (default),
  public-HTTPS, and outbound reverse-tunnel/relay — with **dynamic-DNS** built in,
  because most stations are on **dynamic IP behind NAT**. Relay is the go-to for
  NATed sites that can't port-forward.
- **Calibration & units:** raw ADC is **always the default**; dB is an **optional
  estimate (never automatic)** and SFU/Kelvin require an explicit calibration
  (ships in v1, off by default) — units policy in §6b.
- **Legacy interop:** **three output modes** per instrument/target —
  **legacy** (byte-compatible filenames/headers/`scheduler.cfg`), **standard**
  (clean modern FITS), and **custom** (operator template); a station can ship
  legacy to the central archive and standard/custom to a mirror at the same time.
- **Migration:** existing stations onboard by **import** (config, programs,
  schedule, calibration, in-place FITS indexing), not re-setup — §9a.
- **Timing:** **continuous NTP resync is paramount**, with drift gating and a
  per-class timestamping model — §12a.
- **Failure handling:** one explicit **degrade-don't-die** policy matrix — §14a.
- **Modularity:** strict separation of duties behind versioned contracts; the
  process-isolated plugin boundary also enables **independently-licensed (incl.
  closed) third-party drivers** — §5a / §5b.

**Still open for the product owner:**
1. **Core license** — **GPLv3 vs. AGPLv3** for the core/web app (plugins stay
   independently licensable either way, §5b); and whether a CLA/DCO is required.
2. **Analysis scope** — keep strictly to acquisition/quicklook, or include any
   burst detection/flagging in the suite itself?
3. **Relay infrastructure** — who hosts the reverse-tunnel relay (a shared
   community service vs. self-hosted per institution)? Affects the relay design.
4. **Fleet phase** — when do we add observatory-level oversight across *multiple
   stations*, and is it a hosted dashboard or peer federation?
