# SPDX-License-Identifier: AGPL-3.0-or-later
"""Release hygiene: AGPLv3 license, SPDX headers, governance docs (M24)."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_license_is_agplv3() -> None:
    text = (_ROOT / "LICENSE").read_text()
    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in text
    assert "Version 3" in text


def test_pyproject_license_metadata() -> None:
    pp = (_ROOT / "pyproject.toml").read_text()
    assert 'license = "AGPL-3.0-or-later"' in pp


def test_spdx_headers_on_all_source() -> None:
    missing = [
        str(p.relative_to(_ROOT))
        for p in (_ROOT / "src").rglob("*.py")
        if "SPDX-License-Identifier: AGPL-3.0-or-later" not in p.read_text()
    ]
    assert missing == [], f"missing SPDX header: {missing}"


def test_governance_docs_present() -> None:
    for name in ("GOVERNANCE.md", "CONTRIBUTING.md", "SECURITY.md"):
        assert (_ROOT / name).is_file(), name
    gov = (_ROOT / "GOVERNANCE.md").read_text()
    assert "AGPL-3.0-or-later" in gov
    assert "DCO" in gov  # contributions policy
    assert "closed-source" in gov  # plugin independence


def test_no_env_committed() -> None:
    # the .env must never be tracked (real secrets); .env.example is fine
    assert not (_ROOT / ".env").exists() or (_ROOT / ".env.example").exists()
