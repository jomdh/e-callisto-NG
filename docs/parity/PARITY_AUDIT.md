# Borland Callisto accuracy audit (2026-06-25)

Line-by-line audit of the Windows Borland suite (built *ex profeso* for the
e-Callisto heterodyne device) against e-Callisto NG. Each finding is classified:

- **FIX** — a genuine inaccuracy that breaks device control or archive/JavaViewer
  compatibility. Reproduce the legacy behaviour.
- **ADD** — a legacy capability that is missing and worth having.
- **KEEP** — NG diverges *on purpose* and is correct/safer; document, do not revert.

These all concern the **heterodyne (e-Callisto) path**. SDR drivers are not bound
by them (they may reuse pieces).

## A. Recorder core (callisto.exe: RXRS232 / EEPROM / FitsWrite / mainunit)

| # | Finding | Class |
| -- | -- | -- |
| A1 | **Band-select boundary**: NG uses `<` (171/450); legacy uses `<=`. Wrong band byte at exactly 171.0 / 450.0 MHz. | **FIX** |
| A2 | **`F0` tune format**: `tune_command` emits `F045.0`; legacy `%05.1f` → `F0045.0`. And NF/sweep needs `%6.3f` (1-decimal aliases sub-0.1 MHz steps). | **FIX** |
| A3 | **BUNIT strings**: NG writes `"sfu"`/`"K"`; legacy + JavaViewer key on `"45*log(sfu+10)"`/`"40*log(Tant)"` (`"digits"` matches). | **FIX** (at least legacy output mode) |
| A4 | **10-bit control byte**: legacy forces chargepump-on (0xC6) for 10-bit tuners regardless of config; NG only sets it when `chargepump` is true. | **FIX** |
| A5 | **Firmware detection**: NG invents a "1.7"; rejects unknown devices (legacy defaults to 10-bit / if_init 37.70 and continues); NG default is 8-bit. | **FIX** (default-continue + default 10-bit) |
| A6 | FITS binary-table `TFORM` lacks the `8.3` element; `TSCAL1/2`/`TZERO1/2` cards missing. | **FIX** (legacy mode) |
| A7 | `DATAMIN/DATAMAX` computed from raw values, not the calibrated written image. | **FIX** |
| A8 | rows>8 average/agc/staircase "footer" rows in the image. | **KEEP** (legacy diagnostic quirk; only needed for byte-exact archive) |
| A9 | `TIME-END`/`DATE-END` roll over UT midnight in NG; legacy does not. | **KEEP** (NG is correct) |
| A10 | EEPROM `]`-ack: NG requires it (times out); legacy has a 12 ms fallback. | **KEEP** (NG safer) |
| A11 | if_init constants 37.70 / 36.13, PLL divider math, FE format, CAL parse, SFU/Kelvin math, transpose/low-freq-top, filename. | **ACCURATE** ✓ |
| A12 | Housekeeping (`U2/U4/U6`) reads + state-6 drain-timeout in the acquisition loop. | **ADD** (minor) |

## B. Scheduler / overview / light curves (Scheduler.cpp / mainunit / SchedulerGeni)

| # | Finding | Class |
| -- | -- | -- |
| B1 | **scheduler.cfg import is lossy**: drops the 4th `fprog` (program-switch) column, breaks on alpha modes (A-Z), and collapses multiple intraday entries into one window — losing program/focus switches, mid-day stops, overview lines. | **FIX** |
| B2 | **Horizon-elevation trim**: legacy `delay = horizon/15 h` shrinks the sun window; NG ignores `Station.horizon_deg` for scheduling (uses only `margin_minutes`). | **ADD** |
| B3 | Sun rise/set altitude: NG crosses geometric 0°; legacy uses h0 = −0.8333° (refraction+semidiameter) → events differ several minutes. Also 10-min sampling vs analytic. | **FIX** |
| B4 | **OVS file**: filename lacks `titlecomment` + `_<FCx>`; header drops `pwm`/`version`; no `50<ampl<2500` row gate; freq axis synthesized (not the real sweep). | **FIX** (legacy fidelity) |
| B5 | **LC file**: NG writes variable-width rows for flagged channels only; legacy = fixed 10 columns + `Time_UT` label + `,<version>,pwm=<n>` trailer; title vs instrument token. | **FIX** |
| B6 | No SchedulerGeni-equivalent generator (sunrise-start / transit-restart / sunset-stop / sunset+0.5h overview `scheduler.cfg`). | **ADD** |
| B7 | Scheduled overview (`overview_at`) + program-switch (`program_id`) + fixed/sun windows exist. | **ACCURATE** ✓ (the runtime mechanisms; the import mapping is B1) |

## C. Bench / noise figure (simple / NoiseFigurePlotter)

| # | Finding | Class |
| -- | -- | -- |
| C1 | `F0` precision (same as A2) — collapses fine NF sweep steps. | **FIX** |
| C2 | **`%2`/`%5` format select missing** + NF's `$CRX:<freq>,<mV>` parse path missing (NG only reads `ADC0=`). | **FIX/ADD** |
| C3 | **Integration averaging** (N reads/point) missing; NG takes one read/point. | **ADD** |
| C4 | NF + bandpass divide by a **per-point measured slope**; legacy divides by a **single config `gradient`** constant (`[detector]=`). Different curves on non-flat detectors. | **FIX** (offer the legacy scalar; keep per-point optional) |
| C5 | **AGC LPF + linearity sweeps** (PWM→tuner-gain-voltage via `U2`/`AGC gain=`). | **ADD** |
| C6 | **Time-domain scope / Digitizer** (continuous A0, trigger threshold + beep, CSV log). | **ADD** |
| C7 | Relay settle delay after `fs`; cold/warm/hot codes from config not hardcoded. | **FIX** |
| C8 | Y-factor NF formula (+0.999 guard), detector slope, bandpass-peak-normalize, avg/sigma, `A0`/`O`/`fs` commands. | **ACCURATE** ✓ |

## D. Generator / viewer / wwwgeni (GenFrqPrg / M9703APlotter / wwwgeni)

| # | Finding | Class |
| -- | -- | -- |
| D1 | **frqXXXXX.cfg export entirely missing** — NG stores only a JSON frequency list. Missing: `on_line_testpoint_number=N/2`, `number_of_sweeps_per_second=800/N`, `number_of_measurements_per_sweep=N`, `external_lo`, the header block, and `[NNNN]=FFFF.FFF,lc` channel lines (with the LC flag NG already stores). | **ADD** (biggest gap) |
| D2 | **Nonlinear-start channels** (`nonlinChannels`, default 8; `(N−nonlin)` step denominator; LSB reversal). | **ADD** |
| D3 | **LO converter not wired** into generation — `rf_to_if` exists but `generate_frequencies` takes no converter/LO; no 45-870 validation, no upconverter LO-negation. | **FIX** |
| D4 | No **0.0625 MHz synthesizer-grid** snap in selection; `even` returns bin-center vs legacy bin-edge. | **FIX** |
| D5 | RFI-exclusion drops channels (NG yields < N) vs legacy compacting + keeping N. | **FIX** |
| D6 | Viewer: OVS-specific mV→dB (`/25.4`) path + unit labels (mV/ADU/dB) + typed **Y-axis** zoom missing. | **ADD** |
| D7 | wwwgeni PNG: SFU/dB unit selection + ADU→dB calibration + SFU `[-10,50]` clamp + y-unit label missing; 24-tick UT axis (vs 6h) + dated caption; dated-archive copy; `Lightcurves<title>.png` naming. | **FIX/ADD** |
| D8 | Generator quiet/even modes, RFI band concept, viewer delimiter-detect + LO modes + background-subtract, wwwgeni 10-channel cap. | **ACCURATE** ✓ |

## Headline
The *math and protocol skeleton are faithful*; the inaccuracies cluster in
**exact wire/file formats** (band boundary, F0 width/precision, BUNIT, frq/OVS/LC
file layout, scheduler.cfg modes) and **missing commissioning tools** (AGC sweeps,
scope, frq-file export, horizon trim). These are exactly the things a deployed
e-Callisto operator/archive would notice.
