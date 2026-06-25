# Governance & plugin policy

## License

e-Callisto NG core + web app are licensed **AGPL-3.0-or-later** (ADR-0003). The
suite is served over the network, so AGPL ensures hosted forks contribute their
improvements back. The full text is in [`LICENSE`](LICENSE); every source file
carries `SPDX-License-Identifier: AGPL-3.0-or-later`.

## Plugins may be independently licensed

The AGPL covers the core. **Plugins** -- instrument drivers, upload transports,
output writers, alert channels, time sources -- interact only across **versioned
contracts** (`core.contracts`, `CONTRACT_VERSION`) and, for acquisition, a
**separate supervised process** (ADR-0007). Because a plugin is not a derivative
work of the core across that documented process/contract boundary, a third party
**may ship a closed-source driver** (e.g. for a proprietary FPGA SDR) without it
becoming subject to the AGPL (ADR-0003/0005/0007, DESIGN 5b).

This is the load-bearing reason the boundary is a process + a versioned contract,
not an in-process import.

## Contract policy

- Plugin contracts are **semver-versioned** via `CONTRACT_VERSION`.
- A breaking change is an **ADR + a major bump**; additive changes are minor
  bumps. Third parties build against a pinned contract version.

## Contributions: DCO

Contributions require a **Developer Certificate of Origin** sign-off -- add a
`Signed-off-by: Name <email>` line to each commit (`git commit -s`). No CLA;
copyright stays with contributors. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
