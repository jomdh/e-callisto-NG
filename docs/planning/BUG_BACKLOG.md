# Bug Backlog — e-Callisto NG

Known bugs carry IDs (B1, B2, …). When fixed, move to Resolved with the
commit hash and date.

## Open

| ID | Bug | Found | Notes |
| -- | -- | -- | -- |
| B1 | `sample_rate_hz` semantics inconsistent: `CallistoDriver.configure` uses it as pixels/sec (clock divider), but `Recording.sample_rate_hz` means sweeps/sec (time axis). | S003 | Reconcile in S004 acquisition wiring: configure takes sweeps/sec; clock rate = sweeps x nchannels. Until then the FITS time axis could be wrong for the Callisto path. |

## Resolved

_None yet._
