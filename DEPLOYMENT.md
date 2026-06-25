<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Deploying e-Callisto NG on a station

A station is a Debian/Raspberry Pi OS computer. `scripts/install.sh` turns a
fresh checkout into a running, reboot-surviving station: it **prepares the OS
environment on first run**, installs the suite, and registers the services.

```bash
git clone https://github.com/jomdh/e-callisto-NG.git
cd e-callisto-NG
sudo ./scripts/install.sh          # first run: prepares everything below
```

Everything here is what the installer does (or what you do once for hardware
that needs vendor firmware). Re-running `install.sh` is safe (idempotent).

## 1. System packages (apt)

The installer `apt-get install`s what a fresh Debian lacks:

| Package | Why |
| -- | -- |
| `python3-venv` (matching the system Python, e.g. `python3.12-venv`) | `python -m venv` is not in base Debian; `run.sh`/install fail without it. |
| `python3-pip`, `python3-dev`, `build-essential` | build/install the package + any wheels. |
| `git` | clone / `git pull` updates. |
| `chrony` | NTP discipline — **timing gates recording** (DESIGN §12a); the acquire service waits on `chrony.service`. |
| `usbutils` | `lsusb` for hardware discovery. |
| `soapysdr-tools`, `python3-soapysdr` *(if present in the distro)* | RX-888 / SDR support via SoapySDR. See §5 for the RX-888 driver module. |

## 2. Serial access — the `dialout` group

A serial Callisto on `/dev/ttyUSB*` is owned `root:dialout`. The run user **must
be in `dialout`** or opening the port is denied (`Errno 13`). The installer runs:

```bash
usermod -aG dialout <run-user>
```

A group change only applies to a **fresh login** — the installer's services pick
it up on (re)start, but an interactive shell needs a re-login/reboot.

## 3. ModemManager must not grab the serial port

On desktop Debian, **ModemManager probes every new `/dev/ttyUSB*`** and can hold
a PL2303/FTDI for seconds, breaking the Callisto handshake ("device reports
readiness to read but returned no data"). The installer ships a udev rule that
tells ModemManager to ignore USB-serial bridges:

`/etc/udev/rules.d/99-ecallisto.rules` (installed from `packaging/udev/`):
```
# Let the Callisto's USB-serial bridge be -- ModemManager, keep out.
SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", ENV{ID_MM_DEVICE_IGNORE}="1"
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ENV{ID_MM_DEVICE_IGNORE}="1"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ENV{ID_MM_DEVICE_IGNORE}="1"
```
(If ModemManager isn't installed, this is a harmless no-op. On a headless image
you may also `systemctl mask ModemManager`.)

## 4. USB SDR access (RX-888 and friends)

SDRs are raw USB devices; non-root access needs a udev rule granting the user
(via `plugdev`) read/write. The same rules file adds, for the recognized SDRs:
```
# RX-888 MkII (Cypress FX3), RTL-SDR, Airspy, HackRF, SDRplay
SUBSYSTEM=="usb", ATTRS{idVendor}=="04b4", MODE="0660", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", MODE="0660", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1d50", MODE="0660", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1df7", MODE="0660", GROUP="plugdev"
```
The installer adds the run user to `plugdev` and reloads udev
(`udevadm control --reload && udevadm trigger`).

## 5. RX-888 MkII — vendor firmware (manual, one-time)

The RX-888's Cypress FX3 enumerates as `04b4:00f3` in **DFU/bootloader** until
its firmware is loaded; until then the driver runs in clearly-labelled
**synthetic** mode. The real path is **SoapySDR `driver=rx888`** (what the
station's `rx888.py` reference uses). To make it real:

1. Install **SoapySDR** + the **SoapyRX888** module. SoapyRX888 is usually built
   from source (not in apt):
   ```bash
   sudo apt-get install -y soapysdr-tools libsoapysdr-dev cmake g++ libusb-1.0-0-dev
   git clone https://github.com/<soapyrx888-repo> && cd SoapyRX888
   mkdir build && cd build && cmake .. && make && sudo make install
   ```
2. Confirm the device enumerates:
   ```bash
   python3 -c "import SoapySDR; print(SoapySDR.Device.enumerate('driver=rx888'))"
   # or:  python3 scripts/scan_devices.py
   ```
   When it lists a device, `scan_devices.py` reports **REAL** and the driver
   streams real IQ.

The venv is created with `--system-site-packages` so an apt/conda **SoapySDR**
is visible to the suite without re-installing it in the venv.

## 6. Python environment + app

```bash
python3 -m venv --system-site-packages .venv     # sees system SoapySDR
.venv/bin/pip install -e .                        # the suite + deps
```
First run also writes `.env` (from `.env.example`) with a generated
`ECALLISTO_SECRET_KEY`, a writable data dir, and **`ECALLISTO_RUN_LOOPS_IN_WEB=
false`** so the acquire daemon owns the scheduler/uploader loops (the web app
doesn't double-run them) — see §7.

## 7. Services (systemd) — the two-process model

Acquisition is **independent of the web app** (ADR-0007): the web UI can restart
or crash without stopping recording. Two units, both `Restart=always`,
boot-enabled:

| Unit | Runs | Owns the loops? |
| -- | -- | -- |
| `ecallisto-web` | `uvicorn …app:create_app` on `0.0.0.0:8000` | no (`run_loops_in_web=false`) |
| `ecallisto-acquire` | `ecallisto-ng acquire` (scheduler + uploader) | yes |

The single serial device is shared safely across the two processes by a
**cross-process file lock** (`flock`) on a per-instrument lock file — a record in
one process makes a bench op in the other return a clean "busy", never a
corrupt read.

```bash
systemctl status ecallisto-web ecallisto-acquire
journalctl -u ecallisto-acquire -f
sudo systemctl restart ecallisto-web
```

After a reboot both come back automatically. Open `http://<station-ip>:8000`
and complete the setup wizard (no default credentials).

## 8. Updating

```bash
cd e-callisto-NG && git pull origin main
sudo ./scripts/install.sh      # re-renders units, reinstalls deps, restarts
# or just: sudo systemctl restart ecallisto-web ecallisto-acquire
```
The SQLite schema auto-migrates on start (new columns are added in place), so an
update never needs a DB wipe.

## Quick troubleshooting

| Symptom | Fix |
| -- | -- |
| `Permission denied: /dev/ttyUSB0` | run user not in `dialout` (re-login/reboot after install). |
| "readiness to read but returned no data" | ModemManager grabbed the port (§3), or two openers at once. |
| RX-888 stays `SYNTHETIC` | FX3 firmware not loaded / SoapyRX888 missing (§5). |
| recording flagged/paused | clock not NTP-synced — `chronyc tracking` (§1). |
| service won't start | `journalctl -u ecallisto-web -n50`; check `.env` + venv. |
