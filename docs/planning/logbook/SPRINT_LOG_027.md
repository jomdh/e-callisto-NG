# Sprint 0.3-M9-S027 -- class-3 SDR+FPGA driver + network backend (M9 close)

**Status:** Completed (2026-06-25)  **Branch:** ``0.2-dev``

## Goal / Met?

Record from a network FPGA SDR. **Met** -- `FpgaSdrDriver` ingests device-side
spectra over a `Connection`; `SimulatedFpga` runs it hardware-free; an `sdr_fpga`
instrument records to FITS through the unchanged pipeline.

## Actions Taken

- **D1** `connections/network.py` `NetworkConnection` (TCP, lazy socket).
- **D2** `drivers/sdr/fpga.py` `FpgaSdrDriver` (STX + n-byte frame parser),
  `SimulatedFpga` (emits drifting-peak spectra), `build_fpga_driver`
  (host:port -> network, else simulator).
- **D3** `build_driver` selects `sdr_fpga`; exported from `drivers/sdr`.
- **D4** tests -- conformance/caps (SDR_FPGA/DEVICE/NETWORK); streamed device
  spectra; record an `sdr_fpga` instrument to FITS.

## Verification

Gate green: vulture/black/ruff/flake8/mypy (103 files)/pytest (**105 passed**).

## Milestone M9 -- complete

S026-S027 logged. **All three instrument classes now record through one
pipeline**: class-1 heterodyne (serial), class-2 SDR (host DSP), class-3 SDR+FPGA
(device DSP, network) -- exactly as the M0 driver seam promised, with no change to
the recorder, writer, scheduler, or API. Version -> v0.3.0; tag v0.3.0.

## Lessons

- The `Connection` seam carried a third medium (TCP) cleanly; the FPGA driver
  reused the same buffered-frame-read pattern as the Callisto serial driver.

## Tag

``v0.3.0`` at the M9-complete commit on ``0.2-dev``.
