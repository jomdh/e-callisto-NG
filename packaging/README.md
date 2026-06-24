# Packaging e-Callisto NG

Target: Debian / Raspberry Pi OS (arm64 + amd64). The station is any
Debian-family machine (DESIGN 3), not only a Pi.

## Layout (installed)

```
/opt/ecallisto-ng/           application + .venv
/etc/callisto/ecallisto.env  environment (ECALLISTO_BIND, _PORT, _DATA_DIR, ...)
/var/lib/callisto/           data (FITS, quicklooks)        [user: callisto]
```

## systemd

`systemd/ecallisto-web.service` runs the web app via uvicorn's app factory:

```
uvicorn ecallisto_ng.api.app:create_app --factory --host ... --port ...
```

Install:

```
sudo cp systemd/ecallisto-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ecallisto-web
```

## Quick install (from source)

`scripts/install.sh` creates the user, venv, and directories, installs the
package, and enables the service. Run as root on the target.

## .deb (planned)

A `debian/` packaging dir builds the `ecallisto-ng` package: it places the app
under `/opt`, installs the unit, and creates the `callisto` user + data dirs in
`postinst`. Build with `dpkg-buildpackage`. (Recipe lands in a packaging sprint;
the systemd unit + install script above are the working baseline.)

## Time sync

A station MUST run chrony/NTP and stay synced (DESIGN 12a). The unit orders
after `chrony.service`; provisioning should `apt install chrony` and verify
`timedatectl` shows "System clock synchronized: yes".
