# Contributing

Thanks for helping e-Callisto NG.

## Developer Certificate of Origin (DCO)

By contributing you certify the [DCO](https://developercertificate.org/). Sign
off every commit:

```
git commit -s -m "your message"
```

which adds a `Signed-off-by: Your Name <you@example.org>` trailer. We do **not**
require a CLA; you keep your copyright.

## Workflow

1. Read [`CLAUDE.md`](CLAUDE.md) (the working agreement) and the design.
2. Branch; keep commits small and one logical change each.
3. Run the quality gate before pushing:
   `vulture` → `black --line-length 79` → `flake8` → `ruff check` →
   `mypy` → `pytest`.
4. New source files get `# SPDX-License-Identifier: AGPL-3.0-or-later`.
5. Contract or schema changes need an ADR (`docs/architecture/decisions/`).

## Plugins

Drivers/transports/writers/etc. implement the versioned `core.contracts` and may
be independently licensed -- see [`GOVERNANCE.md`](GOVERNANCE.md).
