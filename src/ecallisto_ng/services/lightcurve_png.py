# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public light-curve PNG renderer (legacy wwwgeni parity, M13).

Reads a daily light-curve file written by ``services.lightcurve`` (header row
of frequencies, then ``UT-hours, v0, v1, ...`` rows) and renders a PNG with a
24-h UT x-axis and up to 10 colored channel traces -- the website image the
legacy ``wwwgeni`` produced. Default 800x496 (legacy ``wwwpar.cfg``).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

# Detector gradient (mV/dB) for the legacy ADU->dB conversion (wwwgeni).
_GRAD_MV_DB = 25.4
# Legacy SFU display clamp (LCBicone.cpp:184-185).
_SFU_MIN, _SFU_MAX = -10.0, 50.0


def _unit(tag: str) -> str:
    """Y-axis unit label for a light-curve tag (audit D7)."""
    return {"SFU": "[SFU]", "KEL": "[K]"}.get(tag, "[dB]")


def _convert(values: list[float], tag: str) -> list[float]:
    """Apply the legacy per-unit transform: SFU clamp, ADU->dB (audit D7)."""
    if tag == "SFU":
        return [min(_SFU_MAX, max(_SFU_MIN, v)) for v in values]
    if tag == "KEL":
        return values
    return [v / _GRAD_MV_DB for v in values]  # ADU -> dB


def _name_parts(stem: str) -> tuple[str, str, str]:
    """(tag, title, yyyymmdd) from an ``LC<date>_<tag>_<title>`` stem."""
    parts = stem.split("_")
    date = parts[0][2:] if parts[0].startswith("LC") else ""
    tag = parts[1] if len(parts) > 1 else "ADU"
    title = "_".join(parts[2:]) if len(parts) > 2 else (parts[-1] or "")
    return tag, title, date


# A readable, distinct palette for the published data product (not UI chrome).
_PALETTE = [
    (220, 50, 47),
    (38, 139, 210),
    (133, 153, 0),
    (211, 130, 0),
    (108, 113, 196),
    (42, 161, 152),
    (203, 75, 22),
    (211, 54, 130),
    (88, 110, 117),
    (181, 137, 0),
]


def _parse(text: str) -> tuple[list[str], list[float], list[list[float]]]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return [], [], []
    freqs = lines[0].split(",")[1:]
    times: list[float] = []
    series: list[list[float]] = [[] for _ in freqs]
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 2:
            continue
        try:
            times.append(float(parts[0]))
        except ValueError:
            continue
        for i in range(len(freqs)):
            try:
                series[i].append(float(parts[i + 1]))
            except (ValueError, IndexError):
                series[i].append(0.0)
    return freqs, times, series


def render_lightcurve_png(
    lc_path: Path, out_dir: Path, width: int = 800, height: int = 496
) -> Path:
    """Render the daily light-curve PNG (legacy wwwgeni parity, audit D7).

    Returns the primary ``<stem>.png`` and also writes the legacy
    ``Lightcurves<title>.png`` plus a dated ``Lightcurves<title>_<date>.png``
    archive copy. SFU files are clamped to [-10, 50]; ADU files are converted
    to dB; the y-axis is labelled with the unit; the x-axis is a 24-hour UT
    grid with even-hour labels.
    """
    freqs, times, series = _parse(lc_path.read_text())
    tag, title, date = _name_parts(lc_path.stem)
    series = [_convert(s, tag) for s in series]

    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 60, 30, width - 150, height - 40
    d.rectangle([x0, y0, x1, y1], outline="black")
    d.text((x0, 8), lc_path.stem, fill="black")
    caption = "Observation Time [UT]" + (f" of {date}" if date else "")
    d.text(((x0 + x1) // 2 - 60, height - 18), caption, fill="black")
    d.text((6, y0), _unit(tag), fill="black")  # y-axis unit label

    flat = [v for s in series for v in s] or [0.0, 1.0]
    ymin, ymax = min(flat), max(flat)
    yspan = (ymax - ymin) or 1.0

    def px(t: float) -> float:
        return x0 + (t / 24.0) * (x1 - x0)

    def py(v: float) -> float:
        return y1 - ((v - ymin) / yspan) * (y1 - y0)

    for h in range(0, 25):  # 24-hour UT grid, label even hours
        x = px(h)
        d.line([x, y1, x, y1 + 4], fill="black")
        if h % 2 == 0:
            d.text((x - 5, y1 + 6), f"{h:02d}", fill="black")

    for i, s in enumerate(series[:10]):
        color = _PALETTE[i % len(_PALETTE)]
        pts = [(px(times[j]), py(s[j])) for j in range(len(times))]
        if len(pts) > 1:
            d.line(pts, fill=color, width=2)
        if i < len(freqs):
            d.text((x1 + 8, y0 + 16 * i), freqs[i], fill=color)

    out = out_dir / f"{lc_path.stem}.png"
    img.save(out)
    # Legacy publication names: live + dated archive.
    img.save(out_dir / f"Lightcurves{title}.png")
    if date:
        img.save(out_dir / f"Lightcurves{title}_{date}.png")
    return out
