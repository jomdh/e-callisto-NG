# Legacy Windows suite — UX/behaviour parity reference

Source of truth for **rebuilding the look, feel, and behaviour** of the Borland
C++Builder Callisto suite in e-Callisto NG, so deployed heterodyne operators keep
their muscle memory. Derived solely from the VCL `.dfm` form definitions +
`.cpp` handlers under `legacy/sources/`. Companion to `WINDOWS_FUNCTIONALITY.md`
(which covers *what* each program does); this covers *how it looks and behaves*.

Every screen quotes exact captions/strings so the NG equivalents can match them.
Where a milestone owns the rebuild, it is tagged `[M11]`..`[M18]`.

> **Colour policy (read first).** Parity here means **layout, controls,
> interaction, and behaviour** — NOT the palette. The legacy colours below are
> recorded only as *evidence of which elements are visually distinguished and
> what they signify*. In e-Callisto NG every colour comes from the shared **M3
> design-system tokens** (Nebula dark / Supernova light); where the legacy used a
> distinct trace/state colour, map it to the nearest **theme semantic token**
> (success/danger) or **chart-series token** — never the literal legacy hue.

---

## 0. The legacy UX language (cross-cutting idioms to preserve)

These recur across every app and define the suite's "feel". Preserve them as the
NG design vocabulary (re-skinned in the M3 system, but behaviourally identical):

1. **The scrolling message log is the primary status surface.** The recorder,
   the installer, and the bench tools all centre on a monospace, timestamped,
   append-only log (`<HH:MM:SS>,$HST:...` / `$CRX:...`). Operators read state from
   it, not from chrome. NG already has this shape in some places; make it a
   first-class, reusable **console panel** component. `[M11]`
2. **One multipurpose progress bar** whose *label* changes meaning with mode
   (`Load =NN%` while recording, `Yield =NN%` during overview, `Timer =NNsec`
   while counting down). Keep the single-bar + mode-label idiom. `[M11]`
3. **Plots distinguish series/scales by colour — using OUR palette.** The legacy
   used a navy field, a yellow raw/digits trace, a lime dB trace, and a
   blue→red waterfall LUT. Keep the *structure* (a dark plot surface, one accent
   trace per series, raw vs dB visually distinct, a perceptual colormap for the
   waterfall) but draw every colour from the **M3 theme + chart tokens** and a
   theme-aligned colormap. `[M13]`
4. **Monospace (Courier New) for live numeric readouts** (times, coordinates,
   voltages). Gives the "instrument" feel. Use a mono token for readouts. `[all]`
5. **Two-state go/no-go semantics** (above/below threshold, connected/lost,
   above/below horizon): the legacy used green vs red. Preserve the *meaning and
   placement*, mapped to the theme's **success / danger semantic tokens**, used
   sparingly. `[M11][M12]`
6. **Live, keystroke-driven control.** Inputs act on `OnChange` (every
   keystroke), clamped to range immediately, sending the command at once — no
   "apply" button on bench/tuning controls. Decide per-field whether to match
   this immediacy or debounce. `[M12]`
7. **Range-edit "zoom".** Plots are zoomed by typing X/Y min/max into four edit
   fields, not by mouse rubber-band (the spectrum viewer). Offer both, but keep
   the typed-range affordance for parity. `[M13]`
8. **Filename-driven semantics.** Units inferred from names (`OVS_` ⇒ mV; else
   ADU/raw); files named `INSTRUMENT_YYYYMMDD_HHMMSS_FC.fit`,
   `LCYYYYMMDD_{ADU|SFU}_<title>.txt`, `OVS_...prn/.csv`. Preserve names. `[M11][M14]`
9. **Sign conventions (carry over exactly):** latitude `>0 = north, <0 = south`;
   **longitude `>0 = WEST, <0 = EAST`** (inverted vs modern GIS); horizon
   "elevation trim" in degrees → `delay = horizon/15` hours. `[M11][M18]`
10. **Utilitarian density.** Titled group-box sections, everything visible on one
    screen, minimal navigation depth. NG re-skins to the M3 themes but keeps the
    dense, single-screen, everything-visible ethos — operators dislike hidden
    state. (Structure/density is the parity target; the grey palette is not.)

---

## 1. callisto.exe — the recorder cockpit  `[M11]`

Title (runtime): `e-Callisto Radiospectrometer  <titlecomment>`. Five windows
(main + XY/XYZ/Yt plots + Info). Main window 346×445, Courier New.

**Main window layout (top→bottom):**
- Menu bar: **Edit** (→ `callisto.cfg`, `scheduler.cfg`) · **Help**
  (`System and Version Infos`, pocket guide, software/construction manual,
  `Open Explorer`, `DeviceManager`, `TaskManager`).
- `Receiverstate` label → becomes `Receiver connected`.
- **Receivermessages** memo — the live `$HST:`/`$CRX:` console (primary status).
- Progress bar + `Percent` label (`Load`/`Yield`/`Timer`).
- `Date` · `Schedulerentry` · `PC-time` row.
- **Main functions** group, exact button captions:
  `Save spectral overview` · `Select frequencyfile` · `Start measurement` ·
  `Stop measurement` (left); `Lightcurve y(t)` · `Spectrum y(f)` ·
  `Spectrum y(f,t)` (right, toggle plot windows).
- Mode radios: **`Automatic`** (default; scheduler on, disables manual buttons) ·
  **`Manual`**.

**Info window** (`Help → System and Version Infos`): flat readout list —
frequency-program file, channels/sweep, sweeps/sec, `Column N of M (=NN.N% of
Ssec filetime)`, time resolution, integration time + clock source, logfile,
focuscode, measurement mode, `Statemachine mainstate = N/6`, disk free
(`NN.NNN percent of drive X: is free: NNNN KB`), version, author.

**Plot windows:**
- **XY — y(f)** 1-D spectrum. Title `Intensity in frequency domain.` X
  `Frequency [MHz]`. Y radios: `dB` (lime, `Relative power [dB]`) /
  **`Digits`** (default, yellow, `log(power) [digit]`). Navy field.
- **XYZ — y(f,t)** waterfall. Title `Intensity in time- &frequency domain.` X
  `Time [sec]` (scrolls right→left), left Y `Channel`, right Y `NNNN MHz`.
  Rainbow LUT + colour bar. Two scrollbars = low/high colour clip (`Lnnn`/`Hnnn`,
  default 0/255). BG-subtraction radios: **`Original`** (default) / `Smooth`
  (105/180) / `Fixed BG`.
- **Yt — y(t)** light-curve. Title `Intensity in time domain.` X `Time [sec]`, Y
  `Relative rf-power [dB]` (auto-scaled). Click the plot → channel list box
  `[NNNN]= ffff.fffMHz` to pick the monitored test frequency.

**Behaviour to replicate:**
- 60 ms master tick; plots redraw ~1/sec, alternating XY+Yt / XYZ to spread load.
- **State machine** 0 idle→1 enable→2 parametrise (Start)→3 open FITS→4 record→5
  disable (Stop)→6 timeout. Start/Stop toggle which buttons are enabled.
- **Data-loss watchdog** (the key robustness UX): on corrupt/over-range data ⇒
  log `$HST:Auto stop due to data loss.` → `$HST:Check RS232-connection!` →
  `$HST:Attempting Auto-Start` (auto-restart). Receiver reset ⇒
  `$HST:Watchdog triggered -> Reset`.
- **Fatal dialogs** (replicate text): body `Check COM-port/USB-adapter` / title
  `Serial port is not responding`; body `Check Callisto power and serial
  connection` / title `Callisto is not responding`; path errors `Path does not
  exist` / `{Logfile|Datafile|Light curve|Spectral overview} path error`.
- **Save spectral overview** = ~45 s 45–870 MHz sweep, progress bar shows
  `Yield`, writes `OVS_*.prn/.csv`, logs `Wait ~45sec please!`.
- Midnight: clear memo, roll logfile.

**NG mapping:** the Operations dashboard + Live Viewer already cover the spirit;
M11 adds the watchdog log+alert, the `Load/Yield/Timer` progress idiom, the
Info-panel readouts, the on-demand overview with OVS output, and the three
labelled live panels (waterfall + `y(f)` + `y(t)`) — the last fully in `[M13]`.

---

## 2. simple — the bench/signal-check tool  `[M12]`

Window `Simple Callisto communication HB9SCT`, 393×218. The canonical
detector-voltage bench UX.

- Buttons `Connect` / `Disconnect`.
- Inputs (label → default): `COM port 1-12` → `COM1`; `Frequency 45-870` `MHz` →
  `151.0`; `Gaincontrol 0-255` `digits` → `150`; `Timebase 20-10000` `msec` → `50`.
- **Detector-voltage indicator:** a thin (17 px) tall **vertical smooth progress
  bar**, range 0–500 (≡ 0–2500 mV, value÷5). The numeric mV shows separately as
  the `Voltage` label → `"<n>mV"`.
- **Trigger:** a vertical track-bar beside the bar (threshold `= 500 −
  position`, inverted so raising the knob lowers the trip point). Label `Trigger`
  → **`rf > trigger`** (lime green) / **`rf < trigger`** (red). Crossing above
  beeps every poll.
- Live: every keystroke sends `F0`/`O`; poll `A0` each tick (`%2` fixed-mV mode).
  Error dialog: title `Communication error` / body `Port does not exist`.

**NG mapping:** Tools → **Detector / Bench** page: freq + gain inputs, a vertical
voltage gauge + numeric mV, a threshold slider with green/red state and optional
audible cue. Drives a `read_detector`/`tune`/`set_gain` driver primitive (ADR).

---

## 3. NoiseFigurePlotter (NF) — RF bench instrument  `[M12]`

Window `Noise Figure Measurement Callisto and Digitizer`, 441×550. Four forms.

- Menus: **FocusControl** (`Reset all` fs00 · `Set all` fs63 · `Sequence` ·
  `Individual`) · **Maintenance** (`Voltages` · `Edit config` · `Show version
  control`) · **Digitizer** · **AGC LPF** · **AGC LIN**.
- Measurement buttons: `Start cold` · `Start warm` · `Start hot` · `Plot raw
  data` · `Plot mV/dB` · `Plot NF` · `Automatic NF` · `Automatic BPF` ·
  `Plot BPF` · `Stop` · `Update config` · `EXIT`.
- Communication group: `Connect`/`Disconnect`, `COM 1-22`.
- Inputs (label → default): `e-Callisto #` (bold 16pt) → `00`; `Fmin [MHz]` 45;
  `Fmax [MHz]` 870; `ENR [dB]` 15; `Att. [dB]` 10.1; `Detector [mV/dB]` 25.4;
  `Number of frequencies` (1–13200) 100; `Number of integrations` 4; `PWM value`
  (1–255) 250; comment line. `Save raw data` checkbox.
- Plot-parameter group: `Y-low`/`Y-high [dB]`, `back color (0-255)`, `yticks`,
  `xticks`, `marker symbol (1-24)`, `line color` (MAGENTA), `thickness curve`,
  `thickness marker`. Output-device radios: **`Screen`** (default) / PDF / EPS /
  GIF / BMP / TIFF / PNG.
- Status: `Portstatus`, `Data` (live `$CRX:freq,mV`), `Errors N`, a `/ \ -`
  spinner, progress bar.
- **Digitizer** (scope) form 1001×364: freq/PWM/focus/sampling inputs;
  `Start`/`Stop`/`Reset plot buffer`/`Close`; `Auto scale`/`Sound on`/`Save data`
  checkboxes; live `Voltage:%6.3f mV`; **vertical** mV bar (0–2500) + **vertical**
  trigger slider with `2500..0` scale; `rf > trigger`(green)/`rf < trigger`(red);
  in-form navy oscilloscope with lime trace, title `Intensity in time domain`.
- **FC** form: six `Set D0..D5` checkboxes + `Enable` (sends `fs%02i`).
- **Voltages** form: live `AGC voltage` / `Emitter BF199 voltage` /
  `Input voltage`, 500 ms refresh.

Measurements (each = a sweep then a plot): **Y-factor NF** (cold/hot, `NF = ENR −
10log10(ylin−0.999)`), **detector slope mV/dB** (warm/hot ÷ Att), **raw overlay**
(cold=blue/warm=green/hot=red), **bandpass** (normalized to peak), **AGC LPF**
(`Minimum should be between 25 and 50`), **AGC linearity** (`no gaps/jumps`).

**NG mapping:** Tools → **Noise figure / Bench** with sub-sections mirroring the
buttons; pure NF/slope/BPF math (tested); charts in the navy/coloured style;
export PNG/CSV; the scope is the same vertical-gauge + trigger pattern as `simple`.

---

## 4. GenFrqPrg — frequency-program generator  `[M14 + M13 plot]`

Window `Generate CALLISTO frequency program out of a spectral overview … V2.4`,
737×368. Grey panels (group boxes), a `.prn` file browser, an independent
**Overview Spectrum Plot** window.

- **Type of converter** radios: **`Direct RX if=rf`** (default; LO field greyed)
  / `Downconverter if=rf-lo (USB)` / `Downconverter if=lo-rf (LSB)` /
  `Upconverter if=rf+lo` (these unlock the LO field).
- **Channel selection method** radios: **`Minimum Detection`** (default;
  quietest/least-RFI sample per window) / `Equally Spaced`.
- **Frequency range to exclude** (RFI band): two horizontal scrollbars `from`/`to`
  with live `45.0000 MHz` readouts (clamped, 0.0625 grid).
- Inputs: `Sweeplength 10...400:` 200 (channel count); `rf-startfrequency [MHz]:`
  45; `rf-stopfrequency [MHz]:` 870; `LO (converter) [MHz]:` 0; `Filenumber
  FRQxxxxx.cfg:` 00001; `Nonlinear Start: No. of Channels:` 8.
- Graph: `Redraw`, `Autoscale`, `Max:`/`Min:` (mV). File ops: `Integrate`,
  `Delete`. Actions: **`Save Program`** (bold), `Preview FrqPrg`, `Refresh List`,
  `Help`, `Exit`, `Put Plot in Forground` (sic).
- **Overview Spectrum Plot** (separate window): navy field; **yellow** overview
  trace; **lime-green** points = selected channels (the quietest-channel
  feedback); **red** vertical lines = the excluded band; left Y `mV`, right Y
  `Chan.`, X `Frequency [MHz]`. Mouse-move title shows `[frequency = NNN.N
  MHz/mV = NNNN]`. Double-click legend: `Yellow=Overview … Green=Generated …
  Red=Excluded …`.
- After save, a dialog: `Please edit headerinformations … You may add most right
  column to produce light curves …` with `Edit Now`/`Skip Editing`.

LO math: Direct `IF=RF`; USB `IF=RF−lo`; LSB `IF=lo−RF` (sweep reversed);
Upconv `RF=IF+lo` (LO written negative). Step grid 0.0625 MHz.

**NG mapping:** the Programs page already auto-generates quiet channels; M14 adds
**LO/converter math + the RFI-exclusion band**, M13 adds the **overview plot with
yellow trace / green selection / red exclusion** overlay and live-cursor readout.

---

## 5. M9703APlotter / Plott_OVS — spectrum viewer  `[M13]`

`SXY-Plotter for *.txt, *.csv and *.prn files … Version 2.0`. Control window
(file browser + settings) + separate plot window `Scope S=g(f)`.

- File browser (drive/dir/file, mask `*.prn;*.txt;*.csv`, multiselect); first
  header line skipped; **delimiter auto-detect** (comma/semicolon/space).
- **Range-edit zoom:** `Y-plottrange [min] [max]` (500/5000), `X-plottrange [min]
  [max]` (45/870) — re-render on every keystroke. Auto-filled from data on load.
- **LO mode** radios: **`RF=LO+IF`** (default) / `RF=LO-IF` / `RF=IF-LO`, with
  `Local oscillator` `MHz` field.
- Checkboxes: `Log scale (dB)` (mV/25.4 for OVS, else 10·log10) ;
  `Subtract minimum` (background floor → 0).
- Buttons: `Save BMP`, `Delete File(s)`, `Reload List`, `Help`, `Exit`.
- Plot: navy field, **yellow** trace, X `Frequency [MHz]`, Y unit `ADU`/`mV`/`dB`,
  title `Intensity of <path>`. Help: `Yellow = Signal-min(Signal) [dB]` + accepted
  formats. Units filename-driven (`OVS_`⇒mV).
- `Plott_OVS` (Python/matplotlib twin): green line, X `Frequency [MHz]`, Y
  `Intensity [mV]`, blue `FM` marker at ~70 MHz, grid; saves `<name>_raw.png`.

**NG mapping:** Tools → **Spectrum viewer** island: load `.prn`/overview, LO mode,
dB/log + background-subtract toggles, typed-range zoom (plus mouse zoom),
PNG export; navy/yellow style; the `FM`-band annotation is a nice parity touch.

---

## 6. SchedulerGeni — sun-relative schedule  `[M11, mostly done]`

`Automatic Scheduler   ETH`, tiny status window (no inputs — reads
`autosched.cfg`). Courier-bold readouts: `Date:`, `Local time:`,
`Sunrise=HH:MM:SS -> scheduler.start HH:MM:SS`,
`Transit= … -> scheduler.restart …`, `Sunset= … -> scheduler.stop …`,
`Monitor= … -> scheduler.ovs …` (only if monitoring). Buttons `Save now` /
`Close`. Output: sorted `scheduler.cfg` (start/restart/stop/overview) rounded to
quarter-hour, horizon trim `delay=horizon/15` h applied to start(+)/stop(−).

**NG mapping:** NG's sun scheduler + preview already covers this. M11's parity add
is the **`8`=overview / restart-at-transit** modes and the four labelled
sunrise/transit/sunset/monitor readouts in the schedule preview.

---

## 7. CallistoInstaller — provisioning  → drives the NG **wizard**  `[M18]`

`Installer Callisto applications and tools … V2.2`, single dense screen (left
inputs, right scrolling log). **Field order = the wizard step order:**

1. Drive · 2. `Serial port COM1...COM24` (`COM11`, with `Check ports`) ·
3. `Filename for FIT-files` (`XCOUNTRY`) · 4. `Title comment application`
(`XTOWN`) · 5. `Instrument location` (`XNAME`) · 6. `Latitude (>0 => north, - =>
south)` (`-40.5`) · 7. `Longitude (>0 => west, - => east)` (`-60.2`) ·
8. `Altitude antenna [m above sealevel]` (`430`) · 9. `Number of instrument
/antenna (00-63)` (`01`) · 10. `Default pwm-level for gain-control (50....255)`
(`120`) · 11. `Elevation of your horizon (-10.° .... 30°)` (`4.5`) ·
12. `FTP login password` · 13. `Create links on the desktop` ✓ · 14. **`Install
Callisto software and configuration files`** (bold primary).

- Live **log + progress bar** on the right (seed `Callisto-xx Installation
  script:`). End message `End of installation … Some parameters probably need to
  be edited manually …`.
- **Uninstall** button (fuchsia danger colour) → confirm dialog `Do you really
  want to erase CALLISTO-NN folders?` / `Warning` / Yes-No-Cancel (destroys all
  data — NG must never replicate the data-loss, but keep the explicit confirm).
- Help text (→ tooltips): FIT name = country code, no special chars except `-`;
  south=negative lat, east=negative lon; reference `http://www.e-callisto.org/`.

**NG mapping:** the M18 wizard uses **this exact field set, order, captions,
defaults, and sign conventions**, grouped into steps (Target → Identity →
Geolocation → Tuning → Network → Review), with the live log/progress pane and a
guarded confirm on any destructive action.

---

## 8. astro — planning aid  `[backlog F8]`

`Astroutility Radioastronomy Group ETH Zürich`. Black/navy sky panel: Cartesian
azimuth(0–360°) × elevation(90°→0°); **lime** source track + cross, **green**
horizon fill, **yellow** geostationary belt, **red** click-marker. Courier-bold
readouts (`Date`, `Local time`, `LST`, `GHA`, `AZI/ELE` green-above/red-below,
`RA+DEC`, `JD`, `TJD`). Popup selectors: `TimeZone` (UT/MEZ/MESZ), `Object`
(Sun/planets/Moon + Cas A/Cyg A/Tau A/Vir A/Sgr A/Orion + manual coords),
`Timestep` (1h/30'/12'/6'). `Redraw`, `BMP`, `About`, `Help`. Low priority.

---

## 9. Parity checklist → NG pages → milestone

| Legacy UX element | NG home | Milestone |
| -- | -- | -- |
| Scrolling `$HST:`/`$CRX:` message console | reusable console panel (Operations + Bench) | M11 |
| Multipurpose progress bar (`Load`/`Yield`/`Timer`) | recorder status | M11 |
| Info-panel readouts (channels, column %, disk, clock, state) | Operations dashboard | M11 |
| Data-loss watchdog + `Check RS232` + auto-restart | acquisition + alert | M11 |
| On-demand/scheduled overview + `OVS_*.prn/.csv` | Tools → Overview | M11 |
| Legacy LC file `LCYYYYMMDD_{ADU|SFU}_<title>.txt`, ≤10 ch | LC writer | M11 |
| Scheduler restart-at-transit + `8`=overview mode | Schedule | M11 |
| Detector bench (vertical mV gauge + green/red trigger) | Tools → Bench | M12 |
| NF / slope / BPF / AGC measurements + charts | Tools → Noise figure | M12 |
| Focus/relay `Set D0..D5` + scope | Tools → Bench | M12 |
| dB view toggle (raw vs dB, visually distinct, raw default) | Live + viewer | M13 |
| Three live panels: waterfall + y(f) + y(t) | Live Viewer | M13 |
| Spectrum viewer (LO modes, dB, bg-subtract, typed zoom, PNG) | Tools → Viewer | M13 |
| Overview plot (yellow/green/red overlay, cursor readout) | Programs | M13 |
| Public light-curve PNG (wwwgeni: SFU/dB, ≤10 colours, 24h UT) | publication | M13 |
| LO/converter math + RFI-exclusion band | Programs generator | M14 |
| SFTP + dated `FITbackup/YYYY/MM/DD` | Distribution | M14 |
| Installer field set/order/captions/sign conventions | Wizard | M18 |
| astro planning panel | (backlog) | F8 |

---

## 10. Hard parity rules (do not "improve" silently)

- Longitude **positive = WEST** in operator-facing fields and `callisto.cfg`
  (signed decimal in `autosched.cfg`). Surface the convention in the label text.
- Trigger threshold is **inverted** vs the slider (`max − position`).
- Detector bar saturates at 2500 mV (value ÷5 over a 0–500 bar).
- Frequency-file flag `,>0` marks a **light-curve** channel (≤10), the test point
  is `channels/2`.
- Units default to **raw/ADU**; dB is an explicit toggle, never automatic (matches
  DESIGN §6b — the legacy XY default is `Digits`, not `dB`).
- Preserve filenames exactly: `INSTRUMENT_YYYYMMDD_HHMMSS_FC.fit`,
  `OVS_*.prn/.csv`, `LCYYYYMMDD_{ADU|SFU}_<title>.txt`, `Lightcurves<title>.png`.
- Keep exact alert/dialog strings (`Check RS232-connection!`, `Callisto is not
  responding`, etc.) so support docs and operator memory still apply.
