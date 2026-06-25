#!/usr/bin/env bash
# Build a flashable Raspberry Pi OS SD-card image with e-Callisto NG preinstalled
# (DESIGN 15). Wraps pi-gen with the project's .deb so a station boots ready to
# run the first-run wizard. Run on a Debian/arm64 builder, not in CI.
#
#   scripts/build-sd-image.sh <ecallisto-ng_VERSION_arm64.deb> [out_dir]
#
# Output: out_dir/ecallisto-ng-<version>.img(.zip)
set -euo pipefail

DEB="${1:?usage: build-sd-image.sh <deb> [out_dir]}"
OUT="${2:-./dist}"
PIGEN="${PIGEN_DIR:-/opt/pi-gen}"

[ -f "$DEB" ] || { echo "deb not found: $DEB" >&2; exit 1; }
command -v git >/dev/null || { echo "git required" >&2; exit 1; }

mkdir -p "$OUT"
if [ ! -d "$PIGEN" ]; then
    echo "== cloning pi-gen into $PIGEN =="
    git clone --depth 1 https://github.com/RPi-Distro/pi-gen "$PIGEN"
fi

# A pi-gen stage that drops in the .deb and enables the services.
STAGE="$PIGEN/stage-ecallisto"
mkdir -p "$STAGE/00-install/files"
cp "$DEB" "$STAGE/00-install/files/ecallisto-ng.deb"
cat > "$STAGE/00-install/00-run.sh" <<'RUN'
#!/bin/bash -e
install -m 644 files/ecallisto-ng.deb "${ROOTFS_DIR}/tmp/ecallisto-ng.deb"
on_chroot <<CHROOT
apt-get update
apt-get install -y /tmp/ecallisto-ng.deb
systemctl enable ecallisto-web ecallisto-acquire || true
rm -f /tmp/ecallisto-ng.deb
CHROOT
RUN
chmod +x "$STAGE/00-install/00-run.sh"
touch "$STAGE/EXPORT_IMAGE"

echo "== building image via pi-gen (this takes a while) =="
( cd "$PIGEN" && IMG_NAME="ecallisto-ng" ./build.sh )

cp "$PIGEN"/deploy/*.img* "$OUT"/ 2>/dev/null || true
echo "== image(s) in $OUT =="
