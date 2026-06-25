# Sprint 0.3-M9-S027 -- class-3 SDR+FPGA driver + network backend (M9 close)

**Sprint Goal:** Record from an FPGA SDR that streams ready spectra over the
network. Closes M9.

**Full ID:** 0.3-M9-S027  **Milestone:** M9 (final)  **Branch:** ``0.2-dev``  **Status:** Planned.

## Deliverables (4)

| # | Task | Layer | Notes |
| -- | -- | -- | -- |
| D1 | `connections/network.py` `NetworkConnection` (TCP) | connections | class-3 link |
| D2 | `drivers/sdr/fpga.py` `FpgaSdrDriver` + `SimulatedFpga` + `build_fpga_driver` | drivers | STX + n-byte spectra framing |
| D3 | register `sdr_fpga` in `build_driver`; export | services/drivers | host:port -> network, else sim |
| D4 | tests + milestone close | tests/docs | conforms/caps; streams device spectra; record via API; v0.3.0 |

## Acceptance Criteria

- [ ] `FpgaSdrDriver` conforms; caps SDR_FPGA / DEVICE / NETWORK.
- [ ] Streams device spectra from the simulator; records to FITS via API.
- [ ] Gate green; SNR clean; M9 tagged v0.3.0.

## Out of Scope

Real FPGA hardware/protocol; USB (vs network) FPGA; M10 fleet view.
