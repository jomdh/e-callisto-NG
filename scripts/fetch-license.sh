#!/usr/bin/env bash
# Vendor the canonical GNU AGPL v3.0 text into LICENSE (ADR-0003).
# The license text is fetched from the authoritative FSF source, never
# transcribed, so it is byte-exact.
set -euo pipefail
cd "$(dirname "$0")/.."
curl -fsSL https://www.gnu.org/licenses/agpl-3.0.txt -o LICENSE
echo "LICENSE updated ($(wc -l < LICENSE) lines)"
