# ADR Index — e-Callisto NG

Canonical register of architecture decisions. **Every ADR commit updates this
index in the same commit.** Status: Proposed | Accepted | Superseded | Open.

| ID | Title | Status |
| -- | -- | -- |
| [ADR-0001](ADR-0001-frontend-portal-not-spa.md) | Frontend: server-rendered portal + JS islands, not a SPA | Accepted |
| [ADR-0002](ADR-0002-units-raw-adc-default.md) | Raw ADC is the default unit; dB/calibration are opt-in | Accepted |
| [ADR-0003](ADR-0003-core-license.md) | Core license: AGPLv3 | Accepted |
| [ADR-0004](ADR-0004-outputwriter-takes-recording.md) | OutputWriter takes a Recording, not loose frames | Accepted |
| [ADR-0005](ADR-0005-bench-capable-contract.md) | BenchCapable: optional bench/commissioning driver contract | Accepted |
| [ADR-0006](ADR-0006-audit-log.md) | Append-only audit log for security-sensitive actions | Accepted |
| [ADR-0007](ADR-0007-acquisition-process-isolation.md) | Acquisition as an isolated, supervised process | Accepted |
| [ADR-0008](ADR-0008-host-hook.md) | Least-privilege host-action hook | Accepted |
| [ADR-0009](ADR-0009-time-source-contract.md) | TimeSource contract (system clock vs GPS/PPS) | Accepted |
| [ADR-0010](ADR-0010-instrument-driver-stability-contract.md) | InstrumentDriver stability contract: typed faults + bounded liveness | Accepted |
| [ADR-0011](ADR-0011-operations-room-ia.md) | Operations-room IA: per-instrument workspace hub + station spine | Accepted |
| [ADR-0012](ADR-0012-remote-instrument-recovery.md) | Remote instrument recovery: liveness escalation to a privileged power-cycle | Accepted |
