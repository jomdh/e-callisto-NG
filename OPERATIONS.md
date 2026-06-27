<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Operating an e-Callisto NG station

For the **operator / maintainer of a deployed station** — the person who runs it
day to day and keeps it healthy, often **remotely**, for a unit that sits alone
in a place no one visits. `DEPLOYMENT.md` covers *installing* a station; this
covers *running* one, and recovering it when something stalls **without physical
access**.

The guiding invariant (DESIGN §14a): **degrade, don't die; never lose
un-uploaded science data; isolate faults; always alert.** Acquisition is
independent of the web app, so the UI can be down while recording continues — and
the reverse can happen too, which §5 is about.

---

## 1. The station at a glance

Two unprivileged systemd services (ADR-0007). Either can restart without
stopping the other:

| Unit | Runs | Owns the record/schedule/upload loops? |
| -- | -- | -- |
| `ecallisto-web` | the portal + API + WebSockets on `:8000` | no |
| `ecallisto-acquire` | scheduler + recorder + uploader | **yes** |

- **Data** lives under `ECALLISTO_DATA_DIR` (FITS files + a `quicklook/` dir);
  the catalog and config are SQLite. Un-uploaded FITS are never deleted.
- **Timing gates recording** (DESIGN §12a): the acquire service waits on
  `chrony`; on clock drift it flags/pauses rather than recording bad timestamps.
- **Raw ADC is the default** (DESIGN §6b) — dB / SFU are opt-in and never
  silently applied.

A station is **healthy** only when all three are true at once:

1. the instrument's state reads **`recording`**, **and**
2. **new FITS files are appearing** (default rollover ~15 min), **and**
3. **live frames are flowing** (the waterfall moves).

State alone is not health — see §5. State is *aspirational* (the loop started);
files and frames are *empirical* (data is really moving).

---

## 2. The portal — the operations room

The portal is the **station operations room**; instruments are central to it
(ADR-0011). The left sidebar has three groups:

- **Operations Room** — the **Dashboard** (cockpit) and one **workspace per
  instrument**. Anything scoped to a single instrument lives in its workspace.
- **Station** — things that span instruments: **Ephemeris**, **Data**,
  **Uploads**, **Diagnostics**.
- **Admin** — users, station settings.

Every instrument carries a station **ID badge `#N`** everywhere it appears
(dashboard tile, workspace header, schedules, programs), so it is always
unambiguous which physical receiver a config applies to.

### Dashboard (cockpit)
One card per instrument: a live mini-waterfall, current **state** badge, next
scheduled action, last upload, and quick actions (**record / stop / overview /
live / open**). Operate from the card for quick actions; click **open ›** for the
full workspace. Per-card messages report the result of each action.

### Per-instrument workspace
Tabs: **Overview · Live · Schedule · Programs · Calibration · Bench** (heterodyne
only) **· Data · Config**.
- **Live** — full WebGL/Canvas waterfall over WebSocket (GPU work runs in *your*
  browser, not on the Pi).
- **Schedule** — recording windows, **owned by this instrument**.
- **Programs / Calibration** — references into the **shared station library**
  (one program can be used by several instruments; the library's *Used by* column
  shows which `#N` reference each).
- **Config** — edit the instrument; **Bench** — heterodyne diagnostics (noise
  figure, sweeps).

---

## 3. Routine operations

- **Record now / stop:** dashboard card or the workspace. A manual record is
  **continuous** until you stop it.
- **Schedule recording:** instrument workspace → **Schedule** → *+ New*. Windows
  are evaluated by the acquire daemon against NTP-disciplined time.
- **Frequency programs:** **Programs** define the channels to sweep. Precedence:
  a record-time override > the instrument's assigned program > the default
  `45 + N` MHz ramp. Assign a program in the instrument's **Config** (or
  workspace **Programs**); it takes effect on the next record loop — restart
  `ecallisto-acquire` to apply immediately to an in-progress run.
- **Calibration sets:** shared library, referenced per instrument; recorded
  products note which level produced them.
- **Browsing data / uploads:** **Station → Data** (filter by instrument) and
  **Station → Uploads** (queue, retry). The uploader retries on its own; a target
  being down never blocks recording.

---

## 4. Monitoring health remotely

- **STALLED is surfaced for you.** A recording instrument stamps a **frame
  heartbeat**; if frames stop, the dashboard tile flips from `recording` to a
  **`stalled`** badge and the workspace Live panel shows **"not responding"**
  instead of a frozen canvas. This is the *empirical* liveness — the heartbeat,
  not the aspirational "recording" label, and not file age. **Do not trust file
  age for liveness:** the recorder buffers a whole ~15-min file in RAM and only
  writes it at rollover, so a healthy station can show a 15-minute-old newest
  file, and a just-flushed file can hide a now-mute device.
- **Diagnostics page** — **Station → Diagnostics** (or `GET
  /api/v1/diagnostics`): one-click self-check that now reads the heartbeat first
  (a `STALLED` warning when frames have stopped), plus parasitic/duplicate
  processes, serial-port contention, service/restart state, clock sync, and disk.
  Offers a downloadable report.
- **From a shell** (through your remote-access method, §6):
  ```bash
  systemctl status ecallisto-web ecallisto-acquire    # both active?
  ls -lt "$ECALLISTO_DATA_DIR" | head                 # newest FITS age
  chronyc tracking                                     # clock disciplined?
  fuser /dev/ttyUSB0                                   # who holds the serial port
  ```
  The authoritative liveness signal is the **`stalled` badge / diagnostics
  heartbeat** above, not file age (which the in-RAM buffer makes unreliable). If
  an instrument reads `stalled`, go to §5.

---

## 5. Remote recovery runbook — when acquisition stalls

This is the part that matters for an **unattended remote station**: getting it
back **with no one on site**. Work the ladder top-down; stop as soon as files
start appearing again. The escalation order matches the driver's own self-heal
contract (ADR-0010) and the host-action boundary (ADR-0008).

> **What you can do without extra privilege:** by default the station user may
> `sudo` **only** the two `systemctl restart` commands (least privilege). Levels
> **L0–L1** need nothing more. **L2–L3** require a true USB power-cycle or reboot,
> which is root — see *The privilege boundary* below.

### How to tell which level you're at
| Signal | Reading |
| -- | -- |
| Web UI loads, dashboard tiles all healthy, just the live panel is blank | L0 (web/UI) — recording is fine. |
| Dashboard tile shows **`stalled`** / Live panel says **"not responding"** | acquisition stalled — the driver self-heals first; if it persists, L1. |
| `stalled` persists after the driver self-heal and an `ecallisto-acquire` restart | device is **hard-wedged at USB** — L2. |
| `lsusb` no longer lists the receiver, or it is stuck in DFU/bootloader | enumeration lost — L2/L3. |

### L0 — Web/UI glitch (data is fine)
Recording is independent of the UI. If only the portal is wrong:
```bash
sudo systemctl restart ecallisto-web      # NOPASSWD-allowed; does NOT touch recording
```

### L1 — Acquisition stalled (state says recording, but nothing is produced)
Restart the acquisition daemon. This **re-runs the whole driver init** — closes
and reopens `/dev/ttyUSB0`, re-identifies, reconfigures:
```bash
sudo systemctl restart ecallisto-acquire  # NOPASSWD-allowed
```
Then confirm a **new** FITS file appears within a rollover and the live waterfall
moves. Avoid restarting twice inside one rollover window — a mid-file restart can
drop the partial file.

> Why restart *individually*, not `restart ecallisto-web ecallisto-acquire`
> together: a wedged unit can stall a combined restart. Bounce the stalled one.

> **The driver self-heals first.** As of the M38 stability work the Callisto
> driver, on a stall, escalates from a soft reset to **closing and reopening the
> OS serial port itself** (what a process restart does) before giving up. Most
> "mute" episodes — including the kind that once needed a manual restart — now
> clear on their own within a stall bound. L1/L2 are for when even that fails.

### L2 — Device mute / hard USB wedge (the headless-site case)
**If L1 and the driver's automatic port-reopen both failed to revive it,** the
receiver is mute at the USB level: the PL2303 still enumerates and the port still
opens, but the device returns no data, and reopening the file handle no longer
helps. The remaining cure is the electrical equivalent of unplug/replug — a
**per-port USB power-cycle** (a true **VBUS** cut) with
[`uhubctl`](https://github.com/mvp/uhubctl), **if the hub supports it**.

> **Reality check — not every hub can do this.** Per-port power switching (PPPS)
> is a hub feature, not a given. On the reference Pi 5 the Callisto sits behind a
> hub (`2-1`, a Genesys bridge) that has **no** PPPS — `uhubctl` reports *"No
> compatible devices detected at location 2-1"* and the VBUS cut is simply
> **unavailable** there. If your unit is the same, a hard mute has **no remote
> power-cut remedy**: rely on the driver self-heal + reboot, and for a guaranteed
> cure **fit a powered USB hub that supports per-port switching** (uhubctl lists
> the known-good models) between the Pi and the receiver. That one hardware
> change is what makes a remote VBUS power-cycle possible.

**Find the right hub/port (discover, don't assume — topology varies per unit):**
```bash
lsusb -t                       # tree: find the Callisto's PL2303 (067b:2303) path
sudo uhubctl                   # lists ONLY hubs that support power switching
```
Match the PL2303 to a hub `location` + `port`. For example, on the reference
Pi 5 the PL2303 sits at USB path `2-1.1` → hub **`2-1`**, **port 1**. Then cut and
restore power to *just that port*:
```bash
sudo uhubctl -l 2-1 -p 1 -a cycle -d 3     # off -> 3 s -> on  (use YOUR location/port)
```
The device re-enumerates fresh as a new `/dev/ttyUSB*`. Finally re-init
acquisition and confirm:
```bash
sudo systemctl restart ecallisto-acquire
ls -lt "$ECALLISTO_DATA_DIR" | head        # a new FITS within a rollover = recovered
```
If the receiver hangs off a hub **without** per-port switching, `uhubctl` won't
list it; power-cycle the nearest switchable upstream hub, or fall through to L3.

### L3 — Last resort: reboot
A reboot re-enumerates USB and restarts both services (boot-enabled). It does
**not** cut VBUS, so it will *not* fix a true L2 mute — but it clears OS-level
gremlins and is the safe fallback when nothing else is reachable:
```bash
sudo reboot
```

### The privilege boundary (why L2/L3 need a deliberate grant)
The station user is intentionally minimal: it can restart the two services and
nothing else. A USB power-cycle (`uhubctl`, `usbreset`, driver unbind/rebind) and
`reboot` are **root**. For an unattended station, choose one:

- **From the portal (installed by `scripts/install.sh`):** the workspace
  **Overview → recover device** button runs the L2 ladder for you — USB
  re-enumerate then a `uhubctl` per-port VBUS power-cycle — through a tightly
  scoped privileged hook (`/usr/local/sbin/ecallisto-hook`, ADR-0008/ADR-0012)
  backed by a **single narrow NOPASSWD sudoers line** for that one script. No
  shell, no sudo password: click it from anywhere the portal is reachable. It
  **reports honestly** — if the hub can't power-cycle (no PPPS), it says
  *"VBUS cut unavailable"* rather than implying a fix; confirm real recovery via
  the `stalled`-clears / heartbeat, not the click. Every recovery is audited.
- **From a shell:** an operator with `sudo` can still run the raw §L2 commands
  over the remote channel (§6) — useful to validate `uhubctl` controls a new
  unit's port the first time.
- **Automated (opt-in — `ECALLISTO_AUTO_RECOVER=true`):** the acquire daemon
  invokes the same hook when a `STALLED` condition persists past the driver's
  self-heal, walking L2→L3 on its own and alerting once a bounded recovery budget
  is spent (so it never loops power-cycles forever). Off by default; turn it on
  per station once the manual button is confirmed to recover the unit.

Either way, **physical access is never required**. If your unit cannot yet do the
automated path, keep the §L2 `uhubctl` command for your specific topology in your
own runbook so recovery is one paste away.

---

## 6. Remote access (prerequisite for everything above)

All of §4–§5 assume you can reach the station. e-Callisto NG does not mandate a
method — use whatever the site allows: a **VPN**, **public HTTPS + DDNS**, or a
**reverse SSH tunnel** out to a jump host (useful when the station is behind NAT
with no port-forwarding). Operator-configured, key-auth only, no default
credentials. Whatever you pick, verify you can both **load the portal** and **get
a shell** before you rely on the station being unattended — L2 recovery needs the
shell.

---

## 7. Quick reference

| Symptom | Level | Action |
| -- | -- | -- |
| Portal wrong, data files still fresh | L0 | `sudo systemctl restart ecallisto-web` |
| State `recording`, no new files/frames | L1 | `sudo systemctl restart ecallisto-acquire`, confirm new FITS |
| L1 didn't help; device mute | L2 | `uhubctl` power-cycle the Callisto's port, then restart acquire |
| `lsusb` lost the device / DFU stuck | L2/L3 | power-cycle port; else reboot |
| Nothing else reachable | L3 | `sudo reboot` |
| Recording flagged/paused | — | clock not synced: `chronyc tracking` (DEPLOYMENT §1) |
| Only records when someone's poking it | — | idle power-saving: re-run `install.sh`/reboot (DEPLOYMENT §7b) |

See also: `DEPLOYMENT.md` (install, services, power-saving), ADR-0007
(process isolation), ADR-0008 (host-action hook), ADR-0010 (driver self-heal),
ADR-0011 (operations-room IA).
